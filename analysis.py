# -*- coding: utf-8 -*-

import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import statsmodels.api as sm
import matplotlib.cm as cm
import matplotlib.colors as colors
import csv


def plot_space_time(agent_pos, 
                    dt = 0.5,
                    space_time_filename = 'space_time'
                    ):
    
    pd.set_option('display.max_columns', None)
    unique_cyclists = agent_pos.AgentID.unique()
    print(unique_cyclists)
    
    agent_pos['Time'] = agent_pos['Step'] * dt
    print(agent_pos)
    fig, ax = plt.subplots(figsize=(6,4), layout='constrained')
    for i in unique_cyclists:
        cyclist_traj = agent_pos[agent_pos.AgentID == i]
        ax.plot(cyclist_traj['Time'], cyclist_traj['Position_x'], color='black', linewidth=0.5)
    ax.set_title(space_time_filename)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Distance (m)')
    ax.set_xlim(1850,2050)
    #2000,2050
    ax.set_ylim(150,250)
    #200,250
    plt.show()  
    
    if type(space_time_filename) is str:
        fig.savefig("figures/" + space_time_filename + "_ST_" + datetime.now().strftime("_%Y-%m-%d_%H%M") + ".png", format='png', dpi=400)


def plot_fd(agent_pos,  # model data frame
            dt = 0.5,  # time step size (s)
            duration = 3600,  # simulation duration (s)
            agg_time = 30,  # aggregation interval for fundamental diagram (s)
            agg_dist = [200, 250],  # aggregation distance / space for fundamental diagram (min and max value in m)
            path_width = 2,
            fd_filename = "fundamental_diagram"):
    
    agg_steps = int(agg_time/dt)
    agent_pos['Time'] = agent_pos['Step'] * dt
    print(agent_pos)
    agg_temp = 0
    agg_intervals = []
    while agg_temp <= (duration/dt):
        agg_intervals.append(agg_temp)
        agg_temp += agg_steps
        
    # for i in agg_intervals
    print(agg_intervals)
    q_k_v = pd.DataFrame(columns=['Time_(s)', 'Flow', 'Density', 'Speed'])
    print(q_k_v)
    
    for i in range(1,len(agg_intervals)):
        # print('\n\n', i)
        agent_pos_temp = agent_pos[(agent_pos['Step'] <= agg_intervals[i]) & (agent_pos['Step'] > agg_intervals[i-1])]
        agent_pos_temp = agent_pos_temp[(agent_pos_temp['Position_x'] <= agg_dist[1]) & (agent_pos_temp['Position_x'] > agg_dist[0])]
        # print(agent_pos_temp)
        unique_cyclists_temp = agent_pos_temp['AgentID'].unique()
        # print(unique_cyclists_temp)
        vkt_sum = 0
        vht_sum = 0
        T = agg_time
        L = agg_dist[1]-agg_dist[0]  # length to derive the FD from
        for j in unique_cyclists_temp:
            agent = agent_pos_temp[agent_pos_temp['AgentID']==j]
            # print(agent)
            d_time = len(agent)*dt
            d_distance = agent['Position_x'].max() - agent['Position_x'].min()
            # print('dt: ', d_time, '; dx: ', d_distance)
            vkt_sum += d_distance
            vht_sum += d_time
        # print(vkt_sum, vht_sum)
        Q = vkt_sum / (T*L)
        K = vht_sum / (T*L)
        if vht_sum != 0:
            V = vkt_sum/vht_sum
        else: V = 0
        new_row = pd.DataFrame({'Time_(s)': [i*agg_time], 'Flow': [Q], 'Density': [K], 'Speed': [V]})
        q_k_v = pd.concat([q_k_v, new_row], ignore_index=True)
    print(q_k_v)
    q_k_v['Flow_(/h/m)'] = (q_k_v['Flow']*3600)/path_width
    q_k_v['Density_(/m2)'] = q_k_v['Density']/path_width
    
    
    '''
    ********************
    *** FIT FD CURVE ***
    ********************
    '''
    # https://www.statsmodels.org/dev/generated/statsmodels.nonparametric.smoothers_lowess.lowess.html
    q_k_v = q_k_v.sort_values(by='Density_(/m2)').reset_index(drop=True)
    # print(q_k_v)
    
    # lowess smoothing flow
    lowess = sm.nonparametric.lowess
    lowess_temp = lowess(q_k_v['Flow_(/h/m)'], q_k_v['Density_(/m2)'], frac=1./2, it=1)
    q_k_v['Flow_Lowess'] = lowess_temp[:,1]
    
    # lowess smoothing speed
    lowess = sm.nonparametric.lowess
    lowess_temp = lowess(q_k_v['Speed'], q_k_v['Density_(/m2)'], frac=1./2, it=1)
    q_k_v['Speed_Lowess'] = lowess_temp[:,1]
    
    
    '''
    ***************
    *** PLOT FD ***
    ***************
    '''
    
    fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, figsize=(5,6))
    
    ax1.scatter(q_k_v['Density_(/m2)'], q_k_v['Flow_(/h/m)'], c=q_k_v['Time_(s)'], cmap='plasma', s=5)
    ax1.plot(q_k_v['Density_(/m2)'], q_k_v['Flow_Lowess'], color='black')
    ax1.set_title(fd_filename)
    ax1.set_ylabel('Bicycle flow (bic/h/m)')
    ax1.set_ylim(0, 3000)
    ax1.set_xlim(0, 0.30)
    norm = colors.Normalize(vmin=q_k_v['Time_(s)'].min(), vmax=q_k_v['Time_(s)'].max())
    scalar_map = cm.ScalarMappable(norm=norm, cmap='plasma')
    scalar_map.set_array([])
    plt.colorbar(scalar_map, ax=ax1, label='Time (s)')
    
    ax2.scatter(q_k_v['Density_(/m2)'], q_k_v['Speed'], c=q_k_v['Time_(s)'], cmap='plasma', s=5)
    ax2.plot(q_k_v['Density_(/m2)'], q_k_v['Speed_Lowess'], color='black')
    ax2.set_ylabel('Bicycle speed (m/s)')
    ax2.set_xlabel('Bicycle density (bic/m²)')
    ax2.set_ylim(0, 6)
    ax2.set_xlim(0, 0.30)
    plt.colorbar(scalar_map, ax=ax2, label='Time (s)')

    # ax1.legend()
    fig.tight_layout()
    plt.show()
    
    if type(fd_filename) is str:
        fig.savefig("figures/" + fd_filename + "_FD_" + datetime.now().strftime("_%Y-%m-%d_%H%M") + ".png", format='png', dpi=400)
        
    # Write states
    #with open("data/" + fd_filename + datetime.now().strftime("_%Y-%m-%d_%H%M") + ".csv", 'w', newline='') as csvfile:
        #writer = csv.writer(csvfile, delimiter=',')
        #writer.writerow(q_k_v['Density_(/m2)'])
        #writer.writerow(q_k_v['Flow_Lowess'])
        #writer.writerow(q_k_v['Speed_Lowess'])
    
    return q_k_v
    
def plot_fd_comp(states,names,fd_filename = "comparison"): 
        
    # read states    
    q_k_v = [None for i in range(len(states))]
    for i in range(len(states)):
        q_k_v[i] = states[i]
    
    '''
    ***************
    *** PLOT FD ***
    ***************
    '''
    
    fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, figsize=(5,6))
    
    colors = ['b','k','g','r']
    for i in range(len(states)):
        ax1.plot(q_k_v[i]['Density_(/m2)'], q_k_v[i]['Flow_Lowess'], color=colors[i], label=names[i])
    ax1.set_title(fd_filename)
    ax1.set_ylabel('Bicycle flow (bic/h/m)')
    ax1.set_ylim(0, 3000)
    ax1.set_xlim(0, 0.30)
    
    for i in range(len(states)):
        ax2.plot(q_k_v[i]['Density_(/m2)'], q_k_v[i]['Speed_Lowess'], color=colors[i])
    ax2.set_ylabel('Bicycle speed (m/s)')
    ax2.set_xlabel('Bicycle density (bic/m²)')
    ax2.set_ylim(0, 6)
    ax2.set_xlim(0, 0.30)

    ax1.legend()
    fig.tight_layout()
    plt.show()
    
    if type(fd_filename) is str:
        fig.savefig("figures/" + fd_filename + datetime.now().strftime("_%Y-%m-%d_%H%M") + ".png", format='png', dpi=400)

    
    
    

