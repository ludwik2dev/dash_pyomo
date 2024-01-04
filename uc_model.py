import os
import pyomo.environ as pyo
import pyomo.gdp as gdp
from dotenv import load_dotenv

import input


def uc_model(units, dev=False):

    load_dotenv()

    # ## Constants
    HOURS = [t for t in range(1, 25)]
    MIN_POWER = 0.4
    OPT_POWER = 0.5
    DEVIATION_COST = 1.25
    BATTERY_EFF = 0.6
    BATTERY_START = 0
    BATTERY_LOAD_TIME = 5  # hours
    START_UP_COST = 10

    demand_profile = { hour+1: value for hour, value in enumerate(input.profiles['demand']) }
    wind_profile = { hour+1: value for hour, value in enumerate(input.profiles['wind']) }
    pv_profile = { hour+1: value for hour, value in enumerate(input.profiles['pv']) }

    plants = { key: val for key, val in units.items() if units[key]['type'] in ['coal', 'gas', 'nuclear'] }
    demand_sources = { key: val for key, val in units.items() if units[key]['type'] in ['demand'] }
    wind_farms = { key: val for key, val in units.items() if units[key]['type'] in ['wind'] }
    pv_farms = { key: val for key, val in units.items() if units[key]['type'] in ['pv'] }
    batteries = { key: val for key, val in units.items() if units[key]['type'] in ['battery'] }

    # if dev:
    #     draw_sources(demand_sources, demand_profile, wind_farms, wind_profile, pv_farms, pv_profile, HOURS)

    def load_bounds(_m, battery, _hour):
        return ( 0, batteries[battery]['power'] )

    def reload_bounds(_m, battery, _hour):
        return ( -batteries[battery]['power'], 0 )

    def power_bounds(_m, plant, _hour):
        return ( 0, plants[plant]['power'] )

    def power_p_bounds(_m, plant, _hour):
        return ( 0, plants[plant]['power'] * OPT_POWER )

    def power_n_bounds(_m, plant, _hour):
        return ( -plants[plant]['power'] * OPT_POWER , 0 )
    
    def vc(m, plant, hour):

        BASE_COST = plants[plant]['vc']
        p_max = plants[plant]['power']
        p_opt = plants[plant]['power'] * OPT_POWER 

        # Negative power
        a_n = BASE_COST * ( DEVIATION_COST - 1 ) / ( p_max * ( MIN_POWER - OPT_POWER ) )
        b_n = -a_n * OPT_POWER * p_max
        x_n = p_opt + m.power_n[plant, hour]
        y_n = cost_n = a_n * x_n + b_n

        # Positive power
        a_p = BASE_COST * ( DEVIATION_COST - 1 ) / ( p_max * ( 1 - OPT_POWER ) )
        b_p = -a_p * OPT_POWER * p_max
        x_p = p_opt + m.power_p[plant, hour]
        y_p = cost_p = a_p * x_p + b_p

        return BASE_COST + cost_n + cost_p

    model = pyo.ConcreteModel()

    # Declare sets
    model.hours = pyo.Set(initialize=HOURS)
    model.plants = pyo.Set(initialize=plants.keys())
    model.demand_sources = pyo.Set(initialize=demand_sources.keys())
    model.wind_farms = pyo.Set(initialize=wind_farms.keys())
    model.pv_farms = pyo.Set(initialize=pv_farms.keys())
    model.batteries = pyo.Set(initialize=batteries.keys())

    # ## Declare variables
    # Plants
    model.power = pyo.Var(model.plants, model.hours, domain=pyo.NonNegativeReals, bounds=power_bounds)
    model.power_p = pyo.Var(model.plants, model.hours, domain=pyo.NonNegativeReals, bounds=power_p_bounds)
    model.power_n = pyo.Var(model.plants, model.hours, domain=pyo.NonPositiveReals, bounds=power_n_bounds)
    model.on = pyo.Var(model.plants, model.hours, domain=pyo.Binary)
    model.start = pyo.Var(model.plants, model.hours, domain=pyo.Integers)
    model.start_p = pyo.Var(model.plants, model.hours, domain=pyo.NonNegativeIntegers)
    model.start_n = pyo.Var(model.plants, model.hours, domain=pyo.NonPositiveIntegers)

    # Batteries
    model.b_volume = pyo.Var(model.batteries, model.hours, domain=pyo.Reals)
    model.b_load = pyo.Var(model.batteries, model.hours, domain=pyo.NonNegativeReals, bounds=load_bounds)
    model.b_reload = pyo.Var(model.batteries, model.hours, domain=pyo.NonPositiveReals, bounds=reload_bounds)
    model.b_power = pyo.Var(model.batteries, model.hours, domain=pyo.Reals)

    # ## Objective - minimize cost of the power system
    model.system_costs = pyo.Objective(
        expr = 
        # Plants variable cost
        + sum( vc(model, plant, hour) for hour in model.hours for plant in model.plants )
        # Plants start-up cost
        + sum( START_UP_COST * model.start_p[plant, hour] * plants[plant]['power'] * plants[plant]['vc'] for hour in model.hours for plant in model.plants )
        # Plants variable cost
        + sum( model.b_load[battery, hour] * batteries[battery]['vc'] for hour in model.hours for battery in model.batteries ), 
        sense=pyo.minimize )

    # ## Demand (has to be fullfilled in each hour, not less not more)
    model.demand = pyo.Constraint(model.hours, rule=lambda m, hour:
        + sum( m.power[plant, hour] for plant in m.plants )
        + sum( -m.b_reload[battery, hour] for battery in m.batteries )
        ==
        + sum( demand_sources[ele]['power'] * demand_profile[hour] for ele in m.demand_sources )
        - sum( wind_farms[ele]['power'] * wind_profile[hour] for ele in m.wind_farms )
        - sum( pv_farms[ele]['power'] * pv_profile[hour] for ele in m.pv_farms )
        + sum( m.b_load[battery, hour] for battery in m.batteries )
    )

    # ## Contsraints
    # Max and min plant power
    model.power_max = pyo.Constraint( model.plants, model.hours, rule=lambda m, plant, hour: m.power[plant, hour] <= plants[plant]['power'] * m.on[plant, hour] )
    model.power_min = pyo.Constraint( model.plants, model.hours, rule=lambda m, plant, hour: m.power[plant, hour] >= MIN_POWER * plants[plant]['power'] * m.on[plant, hour] )
    model.power_opt = pyo.Constraint( model.plants, model.hours, rule=lambda m, plant, hour: m.power[plant, hour] == m.power_n[plant, hour] + m.power_p[plant, hour] + OPT_POWER * plants[plant]['power'])

    # Plant ramp
    model.ramp_up = pyo.Constraint( model.plants, model.hours, rule=lambda m, plant, hour: m.power[plant, hour] <= m.power[plant, hour-1] + plants[plant]['ramp'] if hour > 1 else pyo.Constraint.Skip )
    model.ramp_down = pyo.Constraint( model.plants, model.hours, rule=lambda m, plant, hour: m.power[plant, hour] >= m.power[plant, hour-1] - plants[plant]['ramp'] if hour > 1 else pyo.Constraint.Skip )

    # Plant start up
    model.start_up = pyo.Constraint( model.plants, model.hours, rule=lambda m, plant, hour: m.start[plant, hour] == m.on[plant, hour] - m.on[plant, hour-1] if hour > 1 else m.start[plant, hour] == m.on[plant, hour] )
    model.start_up_partition = pyo.Constraint( model.plants, model.hours, rule=lambda m, plant, hour: m.start[plant, hour] == m.start_p[plant, hour] + m.start_n[plant, hour] )

    # Battery volume
    model.volume_state = pyo.Constraint( model.batteries, model.hours, rule=lambda m, battery, hour: 
        m.b_volume[battery, hour] == m.b_load[battery, hour] * BATTERY_EFF + m.b_reload[battery, hour] + m.b_volume[battery, hour-1] if hour > 1 else
        m.b_volume[battery, hour] == m.b_load[battery, hour] * BATTERY_EFF + m.b_reload[battery, hour] + batteries[battery]['power'] * BATTERY_START * BATTERY_LOAD_TIME
        )

    # Max and min battery volume
    model.volume_max = pyo.Constraint( model.batteries, model.hours, rule=lambda m, battery, hour: m.b_volume[battery, hour] <= batteries[battery]['power'] * BATTERY_LOAD_TIME )
    model.volume_min = pyo.Constraint( model.batteries, model.hours, rule=lambda m, battery, hour: m.b_volume[battery, hour] >= 0 )

    # Max and min battery load and reload
    model.load_max = pyo.Constraint( model.batteries, model.hours, rule=lambda m, battery, hour: m.b_load[battery, hour] <= batteries[battery]['power'] )
    model.reload_min = pyo.Constraint( model.batteries, model.hours, rule=lambda m, battery, hour: m.b_reload[battery, hour] >= -batteries[battery]['power']  )

    # Do not load / reload in the same time
    model.one_direction = gdp.Disjunction( model.batteries, model.hours, rule=lambda m, battery, hour: [ m.b_load[battery, hour] == 0, m.b_reload[battery, hour] == 0 ] )
    pyo.TransformationFactory('gdp.hull').apply_to(model)

    # Sum load and reload
    model.b_sum = pyo.Constraint( model.batteries, model.hours, rule=lambda m, battery, hour: m.b_power[battery, hour] == m.b_load[battery, hour] + m.b_reload[battery, hour] )

    # ## Solve the model
    if os.environ.get("MODE") == 'LOCAL':
        solvername = 'cbc'
        solver = pyo.SolverFactory(solvername, executable='cbc.exe')
    elif os.environ.get("MODE") == 'PRODUCTION':
        solvername = 'glpk'
        solver = pyo.SolverFactory(solvername)
    else:
        raise Exception('MODE in env vars was not supplied.')

    results = solver.solve(model) ## .write()

    # ## Optimalization results 
    if (results.solver.status == pyo.SolverStatus.ok) and (results.solver.termination_condition in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]):

        if dev:
            # Solver status
            print(f'Solver status: {results.solver.status}. Solver termination condition: {results.solver.termination_condition}')
            
            # Cost of the system
            print(f'Cost of the system: {round(pyo.value(model.system_costs), 0)}')

            # Draw plots
            # draw_units(model, plants, batteries, MIN_POWER, OPT_POWER, BATTERY_LOAD_TIME)
            
            # Check variance
            # variance_units(model, plants, OPT_POWER)

        # Summarize results
        model.results = {}
        for unit in model.plants:
            model.results[unit] = {}
            for hour in model.hours:
                power = round(pyo.value(model.power[unit, hour]), 2)
                model.results[unit][hour] = power
        for unit in model.batteries:
            model.results[unit] = {}
            for hour in model.hours:
                power = round(pyo.value(model.b_power[unit, hour]), 2)
                model.results[unit][hour] = -power
        for unit in model.pv_farms:
            model.results[unit] = {}
            for hour in model.hours:
                power = pv_farms[unit]['power'] * pv_profile[hour]
                model.results[unit][hour] = power
        for unit in model.wind_farms:
            model.results[unit] = {}
            for hour in model.hours:
                power = wind_farms[unit]['power'] * wind_profile[hour]
                model.results[unit][hour] = power
        
        return model


    elif (results.solver.termination_condition == pyo.TerminationCondition.infeasible):
        if dev:
            print('Model is infeasible') 
        return False

    else:
        if dev:
            print('Unhandled error. Solver Status: ',  results.solver.status)
        return False


if __name__ == '__main__':
    uc_model(input.units, dev=True)