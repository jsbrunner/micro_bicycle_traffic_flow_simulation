# -*- coding: utf-8 -*-

#%%
'''
********************************************
*** BASE SCENARIO - STRAIGHT PATH (BS-S) ***
********************************************
'''
# Run model
from model import micromodel
BS_S = micromodel(dt = 0.5,
                  data_filename="BS_S",
                  demand=[50,100,150,200,300,350,400,300,200,150,100,50]) 
#50,100,150,200,200,300,300,300,200,150,100,50
#50,100,150,200,300,350,400,300,200,150,100,50
#%% Fundamental diagram
from analysis import plot_fd
BS_S_qkv = plot_fd(BS_S,
        fd_filename="BS-S")
#%% Animation visual
from figures import plot_simulation
plot_simulation(BS_S,
                plot_length=[200,250])
#%% Space-time diagram
from analysis import plot_space_time
plot_space_time(BS_S,
                space_time_filename="BS-S")

#%%
'''
*****************************************
*** PATH WIDTH 1 (PW-1) ***
*****************************************
'''

from model import micromodel
PW_1 = micromodel(data_filename="PW_1",
                  demand=[50,100,150,200,250,300,300,250,200,150,100,50],
                  path_width=1.5) 
#i*0.75 for i in [50,100,150,200,250,275,300,325,250,150,50,0]
#25,50,100,150,200,300,300,200,150,100,50,25
#50,100,150,200,250,300,300,250,200,150,100,50
#%%
from analysis import plot_fd
PW_1_qkv = plot_fd(PW_1,
        fd_filename="PW-1",
        path_width=1.5)
#%%
from figures import plot_simulation
plot_simulation(PW_1,
                plot_length=[200,250],
                path_width=1.5)
#%%
from analysis import plot_space_time
plot_space_time(PW_1,
                space_time_filename="PW-1")
#%%
'''
*****************************************
*** PATH WIDTH 2 (PW-2) ***
*****************************************
'''
# 1.25
from model import micromodel
PW_2 = micromodel(data_filename="PW_2",
                  demand=[50,100,200,300,400,450,450,400,300,200,100,50],
                  path_width=2.5) 
#50,100,150,200,300,600,300,300,200,150,100,50
#50,100,200,300,400,450,500,400,300,200,100,50
#50,100,200,300,400,450,450,400,300,200,100,50
#%%
from analysis import plot_fd
PW_2_qkv = plot_fd(PW_2,
        fd_filename="PW-2",
        path_width=2.5)
#%%
from figures import plot_simulation
plot_simulation(PW_2,
                plot_length=[200,300],
                path_width=2.5)
#%%
from analysis import plot_space_time
plot_space_time(PW_2,
                space_time_filename="PW-2")
#%%
'''
*****************************************
*** PATH WIDTH 3 (PW-3) ***
*****************************************
'''
# 1.35
from model import micromodel
PW_3 = micromodel(data_filename="PW_3",
                  demand=[50,100,200,300,400,500,550,450,300,200,100,50],
                  path_width=3) 
#50,100,150,200,300,600,600,300,200,150,100,50
#50,100,200,300,400,500,550,450,300,200,100,50
#%%
from analysis import plot_fd
PW_3_qkv = plot_fd(PW_3,
        fd_filename="PW-3",
        path_width=3)
#%%
from figures import plot_simulation
plot_simulation(PW_3,
                plot_length=[200,300],
                path_width=3)
#%%
from analysis import plot_space_time
plot_space_time(PW_3,
                space_time_filename="PW-3")



#%%
from analysis import plot_fd_comp
plot_fd_comp([PW_1_qkv,BS_S_qkv,PW_2_qkv,PW_3_qkv],['PW-1','BS-S','PW-2','PW-3'],fd_filename = "PW-comparison")







#%%
'''
*****************************************
*** SPEED DISTRIBUTION 1 (SD-1) ***
*****************************************
'''
# 1.1
from model import micromodel
SD_1 = micromodel(data_filename="SD_1",
                  demand=[50,100,150,200,300,350,400,300,200,150,100,50],
                  v0_sd=0.4) 
#%%
from analysis import plot_fd
SD_1_qkv = plot_fd(SD_1,
        fd_filename="SD-1")
#%%
from figures import plot_simulation
plot_simulation(SD_1,
                plot_length=[200,300])
#%%
from analysis import plot_space_time
plot_space_time(SD_1,
                space_time_filename="SD-1")

#%%
'''
*****************************************
*** SPEED DISTRIBUTION 2 (SD-2) ***
*****************************************
'''
#0.8
from model import micromodel
SD_2 = micromodel(data_filename="SD_2",
                  demand=[50,100,150,200,300,350,400,300,200,150,100,50],
                  v0_sd=1.6) 
#%%
from analysis import plot_fd
SD_2_qkv = plot_fd(SD_2,
        fd_filename="SD-2")
#%%
from figures import plot_simulation
plot_simulation(SD_2,
                plot_length=[50,150])
#%%
from analysis import plot_space_time
plot_space_time(SD_2,
                space_time_filename="SD-2")

#%%
from analysis import plot_fd_comp
plot_fd_comp([SD_1_qkv,BS_S_qkv,SD_2_qkv],['SD-1','BS-S','SD-2'],fd_filename = "SD-comparison")






#%%
'''
*****************************************
*** PASSING THRESOLD 1 (PT-1) ***
*****************************************
'''
# 1
from model import micromodel
PT_1 = micromodel(data_filename="PT_1",
                  demand=[50,100,150,200,300,350,400,300,200,150,100,50],
                  gamma=0.75) 
#%%
from analysis import plot_fd
PT_1_qkv = plot_fd(PT_1,
        fd_filename="PT-1")
#%%
from figures import plot_simulation
plot_simulation(PT_1,
                plot_length=[0,100])
#%%
from analysis import plot_space_time
plot_space_time(PT_1,
                space_time_filename="PT-1")

#%%
'''
*****************************************
*** PASSING THRESOLD 2 (PT-2) ***
*****************************************
'''
# 1
from model import micromodel
PT_2 = micromodel(data_filename="PT_2",
                  demand=[50,100,150,200,300,350,400,300,200,150,100,50],
                  gamma=0.95) 
#%%
from analysis import plot_fd
PT_2_qkv = plot_fd(PT_2,
        fd_filename="PT-2")
#%%
from figures import plot_simulation
plot_simulation(PT_2,
                plot_length=[0,100])
#%%
from analysis import plot_space_time
plot_space_time(PT_2,
                space_time_filename="PT-2")

#%%
from analysis import plot_fd_comp
plot_fd_comp([PT_1_qkv,BS_S_qkv,PT_2_qkv],['PT-1','BS-S','PT-2'],fd_filename = "PT-comparison")







#%%
'''
*****************************************
*** SAFETY REGION 1 (SR-1) ***
*****************************************
'''
# 1.1
from model import micromodel
SR_1 = micromodel(data_filename="SR_1",
                  demand=[50,100,150,200,300,350,400,300,200,150,100,50],
                  alpha=0.6,
                  beta=0.02)
#alpha= 0.5 
#%%
from analysis import plot_fd
SR_1_qkv = plot_fd(SR_1,
        fd_filename="SR-1")
#%%
from figures import plot_simulation
plot_simulation(SR_1,
                plot_length=[200,300])
#%%
from analysis import plot_space_time
plot_space_time(SR_1,
                space_time_filename="SR-1")

#%%
'''
*****************************************
*** SAFETY REGION 2 (SR-2) ***
*****************************************
'''
# 0.9
from model import micromodel
SR_2 = micromodel(data_filename="SR_2",
                  demand=[50,100,150,200,300,350,400,300,200,150,100,50],
                  alpha=1,
                  beta=0.1) 
#alpha= 1.1
#%%
from analysis import plot_fd
SR_2_qkv =plot_fd(SR_2,
        fd_filename="SR-2")
#%%
from figures import plot_simulation
plot_simulation(SR_2,
                plot_length=[200,300])
#%%
from analysis import plot_space_time
plot_space_time(SR_2,
                space_time_filename="SR-2")

#%%
from analysis import plot_fd_comp
plot_fd_comp([SR_1_qkv,BS_S_qkv,SR_2_qkv],['SR-1','BS-S','SR-2'],fd_filename = "SR-comparison")






