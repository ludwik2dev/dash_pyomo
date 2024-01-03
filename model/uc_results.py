import matplotlib.pyplot as plt
import math

# Configuration
plt.rcParams.update({'font.size': 8})

def draw_sources(demand_sources, profile_demand_dct, wind_farms, profile_wind_dct, pv_farms, profile_pv_dct, HOURS):

    # Print demand, renewable and residual load
    res_load = []
    for hour in HOURS:
        dem = sum( [ demand_sources[ele]['power'] * profile_demand_dct[hour] for ele in demand_sources ] )
        wind = sum( [ wind_farms[ele]['power'] * profile_wind_dct[hour] for ele in wind_farms ] )
        pv = sum( [ pv_farms[ele]['power'] * profile_pv_dct[hour] for ele in pv_farms ] )
        diff = round(dem - wind - pv, 0)
        res_load.append(diff)

    sources_len = len( list( demand_sources.keys() ) + list( wind_farms.keys() ) + list( pv_farms.keys() ) ) + 1
    fig, ax = plt.subplots( sources_len, 1 )
    i = 0
    for sources, profile in [(demand_sources, profile_demand_dct), (wind_farms, profile_wind_dct), (pv_farms, profile_pv_dct)]:
        for source in sources.keys():
            ax[i].bar( HOURS, [ sources[source]['power'] * profile[hour] for hour in HOURS], color=sources[source]['color'])
            ax[i].set_title(source, loc='left', y=0.5)
            ax[i].tick_params(axis='x',direction='in', pad=-15)
            ax[i].set_xticks(HOURS, minor=True)
            ax[i].set_xlim(1, max(HOURS))
            i += 1
    ax[i].plot( HOURS, res_load)
    ax[i].set_title('Residual load', loc='left', y=0.5)
    ax[i].plot( HOURS, [ 0 for _hour in HOURS], 'black')
    ax[i].tick_params(axis='x',direction='in', pad=-15)
    ax[i].set_xticks(HOURS, minor=True)
    ax[i].set_xlim(1, max(HOURS))

    plt.show()

    return True


def draw_units(model, plants, batteries, MIN_POWER, OPT_POWER, BATTERY_LOAD_TIME):

    # Plots
    units_len = len( list( model.plants ) + list( model.batteries ) + list( model.batteries ) )
    fig, ax = plt.subplots( units_len, 1 )
    no_plot = 0
    
    # Plants power
    for i, unit in enumerate( model.plants ):
        ax[i].bar( model.hours, [ model.power[unit, hour]() for hour in model.hours], color=plants[unit]['color'])
        ax[i].plot( model.hours, [ plants[unit]['power'] for _hour in model.hours], 'r--')
        ax[i].plot( model.hours, [ plants[unit]['power'] * MIN_POWER for _hour in model.hours], 'r--')
        ax[i].plot( model.hours, [ plants[unit]['power'] * OPT_POWER for _hour in model.hours], color='gray', linestyle='dashed', linewidth=1)
        ax[i].set_title(unit, loc='left', y=0.5)
        ax[i].tick_params(axis='x',direction='in', pad=-15)
        ax[i].set_xticks(model.hours, minor=True)
        ax[i].set_xlim(1, max(model.hours))
        no_plot = no_plot+1

    # Batteries power
    for i, unit in enumerate( model.batteries ):
        ax[i+no_plot].bar( model.hours, [ model.b_power[unit, hour]() for hour in model.hours], color=batteries[unit]['color'])
        ax[i+no_plot].plot( model.hours, [ batteries[unit]['power'] for _hour in model.hours], 'r--')
        ax[i+no_plot].plot( model.hours, [ -batteries[unit]['power'] for _hour in model.hours], 'r--')
        ax[i+no_plot].plot( model.hours, [ 0 for _hour in model.hours], 'black')
        ax[i+no_plot].set_title(unit, loc='left', y=0.5)
        ax[i+no_plot].tick_params(axis='x',direction='in', pad=-15)
        ax[i+no_plot].set_xticks(model.hours, minor=True)
        ax[i+no_plot].set_xlim(1, max(model.hours))
        no_plot = no_plot+1

    # Batteries volume
    for i, battery in enumerate( model.batteries ): 
        ax[i+no_plot].bar( model.hours, [ model.b_volume[battery, hour]() for hour in model.hours], color=batteries[unit]['color'])
        ax[i+no_plot].plot( model.hours, [  batteries[unit]['power'] * BATTERY_LOAD_TIME for _hour in model.hours], 'r--')
        ax[i+no_plot].set_title(f'{battery} volume', loc='left', y=0.5)
        ax[i+no_plot].tick_params(axis='x',direction='in')
        ax[i+no_plot].set_xticks(model.hours, minor=True)
        ax[i+no_plot].set_xlim(1, max(model.hours))
        no_plot = no_plot+1
    
    plt.show()

    return True

def variance_units(model, plants ,OPT_POWER):
    # Variance - how far from optiaml power plants behave
    total = 0
    n = 0
    for plant in model.plants:
        for hour in model.hours:
            power = model.power[plant, hour]()
            opt_power = plants[plant]['power'] * OPT_POWER 
            on = model.on[plant, hour]()

            total = total + math.pow( power / opt_power - 1 , 2 )
            n = n + on

    print(f'Variance: {round( total / n , 2)}')

    return True
