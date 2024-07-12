# A Microscopic Bicycle Traffic Flow Simulation Model Incorporating Cyclists' Heterogeneous Dynamics and Non-lane-based Movement Strategies
Johannes S. Brunner, Ying-Chuan Ni <br />
Traffic Engineering Group, Institute for Transport Planning and Systems, ETH Zürich

## Required Python packages
- Mesa
- Matplotlib
- Pandas
- Statsmodels

Followings are the code in run.py. You can customize the parameters to run the simulation, plot the fundamental diagram, the space-time diagram, and the animation.<br />
## Run the simulation
```
from model import micromodel
model = micromodel(seed = 4,  # random seed
                   duration = 3600,  # simulation duration (s)
                   dt = 0.5,  # simulation time step length (s)
                   demand = [50,100,150,200,300,350,400,300,200,150,100,50],  # list of inflow loading
                   path_width = 2,  # width of the simulated path (m, excl. 2x 0.5 m space on side of the path)
                   v0_mean = 5.2,  # mean of desired longitudinal speed (m/s)
                   v0_sd = 1,  # standard deviation of desired longitudinal speed (m/s)
                   p_mean = 1,  # mean of desired lateral position / distance from right edge +0.5 (m)
                   p_sd = 0.2,  # standard deviation for desired lateral position (m)
                   check_cyclist_id = -1,  # follow the choices of an individual cyclist with his unique_id; put 'False' for no output
                   b_length = 2,  # bicycle length (m)
                   b_width = 0.8,  # bicycle width (m)
                   d_standing = 0.1,  # minimum standing distance to other cyclists (m)
                   a_des = 1.5,  # relaxation time for acceleration (s)
                   b_max = 3,  # maximum braking (m/s^2, >0)
                   omega_max = 0.3,  # maximum lateral speed (m/s)
                   omega_des = 0.15,  # desired lateral speed (m/s)
                   d_omega_max = 0.2,  # maximum lateral acceleration (m/s^2)
                   phi = 4,  # coefficient of the length of the consideration range
                   alpha = 0.8,  # coefficient of the length of the safety region
                   beta = 0.06,  # coefficient of the width of the safety region
                   gamma = 0.85,  # passing threshold
                   data_filename = "simulation_data",  # type 0 if file should not be saved
                   demand_input = 'stochastic')
```

## Plot the fundamental diagram
```
from analysis import plot_fd
model_qkv = plot_fd(model, 
                    dt = 0.5,  # time step size (s)
                    duration = 3600,  # simulation duration (s)
                    agg_time = 30,  # aggregation interval for fundamental diagram (s)
                    agg_dist = [200, 250],  # aggregation distance for fundamental diagram (min and max value in m)
                    path_width = 2,
                    fd_filename = "model")
```

## Plot the space-time diagram
```
from analysis import plot_space_time
plot_space_time(model, 
                dt = 0.5,
                space_time_filename = "model")
```

## Plot the animation
```
from figures import plot_simulation
plot_simulation(model, 
                dt = 0.5,
                path_width = 2,
                anim_interval = 500, # time to update (ms); 500 ms = 2 FPS
                plot_length = [0,300],  # start and end of space to show the simulation (m)
                check_cyclist_id = -1, 
                animation_filename = "model")
```

## Citation
Please cite this article if you use this model in your work:<br />
Brunner, J. S., Ni, Y.-C., Kouvelas, A., & Makridis, M. A. (2024). Microscopic simulation of bicycle traffic flow incorporating cyclists’ heterogeneous dynamics and non-lane-based movement strategies. _Simulation Modelling Practice and Theory_, _135_, 102986.<br />
https://doi.org/10.1016/j.simpat.2024.102986

