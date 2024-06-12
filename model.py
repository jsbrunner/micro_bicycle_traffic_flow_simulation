# -*- coding: utf-8 -*-


'''
******************************************************
*** MODEL FILE (no need to change parameters here) ***
******************************************************
'''
#%%
from mesa import Agent, Model
from mesa.time import SimultaneousActivation
from mesa.space import ContinuousSpace
from mesa.datacollection import DataCollector
from datetime import datetime
import pandas as pd
import random
import math
import sys
#%%

def micromodel(seed = 4,  # random seed
               duration = 3600,  # simulation duration (s)
               dt = 0.5,  # simulation time step length (s)
               demand = [50,100,150,200,250,300,350,400,300,200,100,50],  # list of inflow loading
               path_width = 2,  # width of the simulated path (m, excl. 2x 0.5 m space on side of the path)
               bottleneck_width = 0,  # (m); put numbers [1.0,1.5,2.0] for the bottleneck to be active; all other values mean that the bottleneck is not active
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
               lookback = 1,  # proportion of cyclists looking back before moving laterally [0,1]
               side_obstacle = 0.2,  # width deducted from both sides of the extended path to simulate obstacles (m)
               data_filename = "simulation_data",  # type 0 if file should not be saved
               demand_input = 'stochastic'):
    
    ''' 
    **********************
    *** COMPUTE INFLOW ***
    **********************
    ''' 
    
    # We assume that bicycles are generated with a same interval (uniformly distributed) according to the demand.
    path_width += 1
    random.seed(seed)  # set the seed
    time_steps = int(duration/dt)
    inflow_step = []  # time points that bicycles enter the bike lane
    
    # fixed interval
    if demand_input=='fixed':
        correct = True
        if time_steps % len(demand) != 0:
            correct = False
        for i in demand:
            if i == 0:
                print("Input warning: Demand cannot be 0, set 1 instead.")
                sys.exit()
            if (time_steps/len(demand)) % i != 0:
                correct = False
        if correct:
            splits = len(demand)
            interval = [int((time_steps/splits) / demand[i]) for i in range(len(demand))] # Time interval in both of the two slots
            print(interval)
            for i in range(len(demand)):
                inflow_step.extend(list(range(0 + int(time_steps/splits) * i, int(time_steps/splits) * (i+1), interval[i])))
            print(inflow_step, len(inflow_step))
        else:
            print("Input warning: time steps cannot be divided up by demand. Choose values so that the number of time steps (duration/dt) is a multiple of both, the length of the demand list and each individual demand value in the list.")
            sys.exit()
    
    # stochastic interval
    elif demand_input=='stochastic':
        splits = len(demand)
        for i in range(len(demand)):
            probability = demand[i]/(time_steps/splits)
            print(probability)
            for j in range(int(time_steps/splits)):
                rng = random.random()
                if rng < probability:
                    inflow_step.append(0 + int(time_steps/splits) * i + j)
        print(inflow_step, len(inflow_step))

    ''' 
    *******************
    *** AGENT CLASS ***
    *******************
    '''
    
    class Bicycle(Agent):
        
        ''' 
        ************************************
        *** INITIALIZATION AND VARIABLES ***
        ************************************
        '''
        
        def __init__(self, unique_id, model):
            super().__init__(unique_id, model)
            
            # Fixed attributes
            self.unique_id = unique_id
            self.length = b_length  # bicycle length
            self.width = b_width  # bicycle width
            
            # self.v0 = random.uniform(v0_mean-v0_sd, v0_mean+v0_sd)  # distribution of desired lateral position
            # self.v0 = random.triangular(v0_mean-v0_sd, v0_mean+v0_sd, v0_mean)
            # truncate gaussian distribution at +- 2 sd
            self.v0 = 0
            while (self.v0 < v0_mean-2*v0_sd) or (self.v0 > v0_mean+2*v0_sd):
                self.v0 = random.gauss(v0_mean, v0_sd)
            self.p = random.uniform(p_mean-p_sd, p_mean+p_sd)  # distribution of desired lateral position
            self.a_des = a_des  # feasible relaxation time for acceleration
            self.b_max = b_max  # m/s**2 maximum braking force (positive value)
            
            self.omega_max = omega_max  # m/s fixed value for the maximum lateral speed
            self.omega_des = omega_des  # m/s fixed value for the desired lateral speed
            self.d_omega_max = d_omega_max   # m/s^2 fixed value for the maximum lateral acceleration
    
            self.alpha = alpha  # scale length of safety region
            self.beta = beta  # scale width of safety region
            self.gamma = gamma  # passing threshold
            self.phi = phi # coefficient for consideration range (caution with the var name)
                       
            
            ''' Dynamic attributes (these following values initialize the simulation) '''
            self.overtake = False
            self.pos = (0, self.p)  # Current position, a "tuple" type position variable is required by Mesa and used in its other built-in function
            self.speed = self.v0  # Current (actual) longitudinal speed
            self.acceleration = 0  # actual longitudinal acceleration/braking for the current time step
            self.v_lat = 0  # actual lateral speed for the current time step
            self.v_lat_prev = 0  # previous lateral speed
            self.next_speed = 0
            self.restr_lat_speed = 0
            self.hyp_angle = 0
            self.next_coords = (0, self.p)  # Attribute which stores the determined next coordinates
            self.sr_length = self.length/2 + 0.1 + self.v0*self.alpha  # length of the safety region
            self.sr_width = self.width/2 + 0.1 + self.v0*self.beta  # width of the safety region
            self.cr_length = 4 + self.v0*self.phi  # consideration range length
            # auxiliary variables
            self.cat1_cyclists = []  # list of significantly slower cyclists in consideration range
            self.cat12_cyclists = []  # list of slightly slower cyclists in consideration range
            self.cat3_behind = []  # list of faster cyclists in the backward view
            self.all_lateral = [] # list of cyclists in the forward view to prevent lateral collision with
            self.blocked_space_indiv = []  # auxiliary list used across level 1 and 2
            self.des_lat_pos = 0  # desired lateral position
            self.trajectory = []  # list including the coordinates for the desired path (therefore also implicitly the moving angle)
            self.leader = 0  # variable to save leading cyclist's object id
            self.leader_details = []
            self.cut_off_flag = False  # True if cyclist would cut-off somebody else
            if random.random() <= lookback:
                self.do_look_back = True
            else:
                self.do_look_back = False
        
        ''' 
        *********************
        *** GET FUNCTIONS ***
        *********************
        '''
        # get position of a bicycle object
        def getPos(self):
            return [self.pos[0],self.pos[1]]
        
        # get speed of a bicycle object
        def getSpeed(self):
            return self.speed
        
        ''' 
        ***************************
        *** AUXILIARY FUNCTIONS ***
        ***************************
        '''
        
        
        def findCat1(self):
            neighbors = self.model.space.get_neighbors(self.pos,self.cr_length+10,False) # add 10 metres so that the circular radius does not matter anymore
            leaders = [l for l in neighbors if l.getPos()[0] > self.pos[0] and l.getPos()[0] < (self.pos[0]+self.cr_length)] # obtain cyclists in consideration range
            self.cat1_cyclists = [l for l in leaders if l.getSpeed() <= (self.gamma*self.v0)] # obtain cat1 cyclists
        
        def findCat12(self):
            neighbors = self.model.space.get_neighbors(self.pos,self.cr_length+10,False) # add 10 metres so that the circular radius does not matter anymore
            leaders = [l for l in neighbors if l.getPos()[0] > self.pos[0] and l.getPos()[0] < (self.pos[0]+self.cr_length)] # obtain cyclists in consideration range
            self.cat12_cyclists = [l for l in leaders if l.getSpeed() <= (self.v0)] # obtain cat1 and cat2 cyclists
        
        def findCat3Behind(self):  # not really cat 3 but the cyclists that are currently faster than you are
            neighbors = self.model.space.get_neighbors(self.pos,20,False)
            followers = [l for l in neighbors if l.getPos()[0] < self.pos[0] and l.getPos()[0] > (self.pos[0]-20)] # obtain cyclists in backward view
            self.cat3_behind = [l for l in followers if l.getSpeed() > (self.getSpeed())] # obtain cat3 cyclists
        
        def findAllLateral(self):  # all cyclists in the lateral collision prevention zone
            neighbors = self.model.space.get_neighbors(self.pos,self.cr_length+10,False)
            self.all_lateral = [l for l in neighbors if l.getPos()[0] >= self.pos[0] and l.getPos()[0] < (self.pos[0]+self.sr_length)] # obtain cyclists in the lateral collision prevention zone

        ''' 
        ************************
        *** UPDATE FUNCTIONS ***
        ************************
        '''
        
        # Calculate and update the attributes in the next step
        def calPos(self): 
            if isinstance(self.unique_id, str):  # exclude cyclists from virtual bottleneck from calculations and updating
                self.speed, self.acceleration, self.v_lat = 0, 0, 0
            if self.speed*dt + self.acceleration*dt <= 0:
                self.acceleration = -self.speed
            self.next_coords = (self.pos[0] + self.speed*dt + self.acceleration*0.5*dt**2, self.pos[1] + self.v_lat*dt)  # new x and y position values
            if self.overtake == True:
                self.model.sum_lat_dist += abs(self.v_lat*dt)
        
        # Determine and update the next speed
        def calSpeed(self):
            if isinstance(self.unique_id, str):  # exclude cyclists from virtual bottleneck from calculations and updating
                self.speed, self.acceleration, self.v_lat = 0, 0, 0
            self.next_speed = self.speed + self.acceleration * dt # apply acceleration from ndm
        
        def calLatSpeed(self):
            if self.restr_lat_speed == 0:
                self.v_lat = 0
            elif self.restr_lat_speed != 0 and self.v_lat > 0:
                self.v_lat = min(self.next_speed * self.hyp_angle, self.restr_lat_speed)
            else:
                self.v_lat = max(self.next_speed * self.hyp_angle, self.restr_lat_speed)
        
        def updateCR(self):
            self.cr_length = 4 + self.phi*self.next_speed
        
        def updateSR(self):
            self.sr_length = self.length/2 + 0.1 + self.alpha*self.next_speed
            self.sr_width = self.width/2 + 0.1 + self.beta*self.next_speed

        ''' 
        ***********************
        *** LEVEL FUNCTIONS ***
        ***********************
        '''
        
        ''' LEVEL 1: Desired lateral position '''
        def findLatPos(self): 
            if self.unique_id==check_cyclist_id: print("\n****** LEVEL 1: LATERAL POSITION ******")
            self.model.num_all_decision += 1
            # find cat1 cyclists in consideration range
            self.findCat1()
            # if there is no cat. 1 cyclist in the consideration range
            if len(self.cat1_cyclists)==0:  
                self.des_lat_pos = self.p  # just go to the desired lateral position
                self.overtake = False
                if self.unique_id==check_cyclist_id: print("No cat. 1 leader, des_lat_pos={}".format(round(self.des_lat_pos,2)))
            else:
                self.overtake = True
                self.model.num_decision = self.model.num_decision + 1
                self.blocked_space_indiv = []  # empty list the touples with lateral positions of cat1 cyclists
                unblocked_space = []  # will contain the borders and width of the lateral gap(s)
                
                # obtain lateral positions blocked by cat. 1 cyclists in consideration range
                for i in self.cat1_cyclists:
                    self.blocked_space_indiv.append((i, i.getPos()[1]-self.width/2, i.getPos()[1]+self.width/2))  # change 0.4 to the actual width including stabilization
                    
                self.blocked_space_indiv.sort(key=lambda a: a[2], reverse=True)  # sort cyclists from left to right                
                
                # boolean to terminate the following loop (searching for a wide-enough lateral gap)
                gap_found = False
                
                while gap_found==False:
                    # if the path is narrow so that the only blocking cyclist is removed, there needs to be a criterion
                    if len(self.blocked_space_indiv)==0:
                        unblocked_space.append([path_width-side_obstacle,side_obstacle,path_width-2*side_obstacle])
                        self.des_lat_pos = self.p
                        break
                    
                    # find gaps/unblocked spaces between cyclists
                    for i in range(len(self.blocked_space_indiv)):
                        # if it is the first cyclist from the left
                        if i==0: 
                            unblocked_space.append([path_width-side_obstacle, self.blocked_space_indiv[i][2], round(path_width-self.blocked_space_indiv[i][2],2)])  # also add width of the gap 
                        elif self.blocked_space_indiv[i-1][1] <= self.blocked_space_indiv[i][2]:  # if the projection overlaps, there is not an additional unblocked space
                            continue
                        else: # add an additional unblocked space
                            unblocked_space.append([self.blocked_space_indiv[i-1][1], self.blocked_space_indiv[i][2], round(self.blocked_space_indiv[i-1][1]-self.blocked_space_indiv[i][2],2)])
                    unblocked_space.append([self.blocked_space_indiv[-1][1], side_obstacle, round(self.blocked_space_indiv[-1][1],2)])  # add a final gap towards the right of the path                    
                    
                    # check if there is a gap big enough to fit, including safety region (left to right priority, list is already sorted alike)
                    for i in unblocked_space:
                        if i[2] >= 2*self.sr_width:
                            self.des_lat_pos = i[1]+self.sr_width
                            gap_found = True
                            break
                    if gap_found==True:
                        break
                    
                    # remove cyclist the furthest downstream if no gap is found
                    furthest_agent_pos = 0
                    furthest_agent = ...
                    for i in range(len(self.blocked_space_indiv)):
                        if self.blocked_space_indiv[i][0].getPos()[0] > furthest_agent_pos:
                            furthest_agent_pos = self.blocked_space_indiv[i][0].getPos()[0]
                            furthest_agent = i
                    
                    # delete furthest downstream cyclist from the list of blocking cyclists
                    del self.blocked_space_indiv[furthest_agent]
                if self.unique_id==check_cyclist_id: print("Cat. 1 present, des_lat_pos={}".format(round(self.des_lat_pos,2)))
    
        ''' LEVEL 2: Moving angle and leader '''
        def findTraj(self):  
            if self.unique_id==check_cyclist_id: print("\n****** LEVEL 2: TRAJECTORY ************")
            # compute lateral movement distance to reach the desired position
            req_lat_move = self.des_lat_pos - self.getPos()[1]  # desired position minus actual position -> gives direction left or right directly
            obstr_cyclists = []  # cyclists potentially obstructing from reaching desired position
            if self.unique_id==check_cyclist_id: print("Reg_lat_move={}".format(round(req_lat_move,2)))
            # case with no slower cyclists
            if len(self.cat1_cyclists)==0: 
                # move the desired lateral speed to the position
                if abs(req_lat_move) < self.omega_des:  # handle case where desired lateral speed would overshoot the position within one time step
                    self.v_lat = req_lat_move
                else:  # when the required lateral distance is not covered in one time step, handle whether to move right or left at desired lateral speed
                    if req_lat_move < 0:
                        self.v_lat = -self.omega_des
                    else:
                        self.v_lat = self.omega_des
                if self.unique_id==check_cyclist_id: print("No cat. 1 leader, v_lat={}".format(round(self.v_lat,2)))
            else: # case with slower cyclists remaining                
                # remove cat. 1 cyclists that are not influencing the potential trajectory
                remove_indices = []
                for i in range(len(self.blocked_space_indiv)):
                    obstr_cyclists.append(self.blocked_space_indiv[i][0])  # append cyclist object from the remaining cat. 1 cyclists
                
                # find non-obstructing cyclists depending on the direction of lateral movement
                for i in range(len(obstr_cyclists)):  
                    if req_lat_move < 0:  # when moving to the right
                        if obstr_cyclists[i].getPos()[1] > self.getPos()[1]+1 or obstr_cyclists[i].getPos()[1] < self.des_lat_pos-1:
                            remove_indices.append(i)
                    else:  # when moving to the left
                        if obstr_cyclists[i].getPos()[1] < self.getPos()[1]-1 or obstr_cyclists[i].getPos()[1] > self.des_lat_pos+1:
                            remove_indices.append(i)
                
                # remove cycists not influencing the trajectory
                for i in sorted(remove_indices, reverse=True):
                    del obstr_cyclists[i]
                
                # if there is no obstructing cyclist, do the same as above and go towards the desired position at the end of the CR
                if len(obstr_cyclists)==0:
                    if abs(req_lat_move) < self.omega_des:
                        self.v_lat = req_lat_move
                    else:
                        if req_lat_move < 0:
                            self.v_lat = -self.omega_des
                        else:
                            self.v_lat = self.omega_des
                            
                else: # if there are obstructing cyclists, project these cyclists to when you would pass
                    for i in range(len(obstr_cyclists)):
                        # calc dist to passing point
                        p1 = self.getPos()[0]
                        v1 = self.v0
                        p2 = obstr_cyclists[i].getPos()[0]
                        v2 = obstr_cyclists[i].getSpeed()
                        time_to_pass = 10000
                        if isinstance(self.unique_id, str):
                            time_to_pass = 10000
                        else:
                            time_to_pass = (p2-p1)/(v1-v2)
                        dist_to_pass = v1*time_to_pass
                        
                        # calculate lateral passing point
                        lat_passing_point = 0
                        if req_lat_move < 0:
                            lat_passing_point = obstr_cyclists[i].getPos()[1]-(self.width+self.sr_width) # one meter to the right of the center
                        else:
                            lat_passing_point = obstr_cyclists[i].getPos()[1]+(self.width+self.sr_width) # one meter to the right of the center
                        # calc moving angle (which angle is the absolute steepest)
                        angle_temp = math.atan2((lat_passing_point-self.getPos()[1]), dist_to_pass)
                        obstr_cyclists[i] = [obstr_cyclists[i], abs(angle_temp), dist_to_pass, lat_passing_point-self.getPos()[1]]
                    
                    # go for the steepest angle (which angle is the absolute steepest)
                    steepest_angle_temp = 0
                    for i in range(len(obstr_cyclists)):
                        if obstr_cyclists[i][1] > steepest_angle_temp:
                            steepest_angle_temp = obstr_cyclists[i][1]
                    
                    # actually required lateral speed
                    if req_lat_move < 0:
                        self.v_lat = -(self.getSpeed()*math.tan(steepest_angle_temp))
                    else:
                        self.v_lat = (self.getSpeed()*math.tan(steepest_angle_temp))
                    
            
            # "look-back" module: do not cut-off cyclists that are too close to avoid a collision
            if (self.do_look_back) & (self.getSpeed() > 0.5):
                self.findCat3Behind()
                proj_Cat3Behind = []
                if req_lat_move <= 0:
                    proj_Cat3Behind = [l for l in self.cat3_behind if l.getPos()[1] <= self.pos[1] and l.getPos()[1] > (self.des_lat_pos-self.width)]
                else:
                    proj_Cat3Behind = [l for l in self.cat3_behind if l.getPos()[1] > self.pos[1] and l.getPos()[1] < (self.des_lat_pos+self.width)]
                # for each of those cyclists, check if they are able avoid a collision with their braking power when cut off; this is a very aggressive variant, because it does not consider any politeness to let others overtake first
                required_braking = 0
                for i in proj_Cat3Behind:
                    required_braking = ((i.getSpeed()-self.getSpeed())**2) / (2*((self.getPos()[0]-i.getPos()[0])-self.length))
                    if 2*required_braking > self.b_max:
                        self.v_lat = 0
                        self.cut_off_flag = True
                
                lateral_neighbors = self.model.space.get_neighbors(self.pos,self.length,False)
                if req_lat_move <= 0:
                    lateral_neighbors = [l for l in lateral_neighbors if l.getPos()[1] < self.getPos()[1]]
                else:
                    lateral_neighbors = [l for l in lateral_neighbors if l.getPos()[1] > self.getPos()[1]]
                
                if len(lateral_neighbors) != 0:
                    self.v_lat = 0 
                    self.cut_off_flag = True
            
                if self.unique_id==check_cyclist_id: print("Cyclists behind={}, required braking={}, b_max={}, v_lat={}".format(proj_Cat3Behind, required_braking, self.b_max, self.v_lat))
                if self.unique_id==check_cyclist_id: print("Lateral_neighbors: ", [i.unique_id for i in lateral_neighbors])
            
            # feasible lateral speed (restricted by max lateral speed and acceleration)
            max_speed_left = self.v_lat_prev + self.d_omega_max*dt
            max_speed_right = self.v_lat_prev - self.d_omega_max*dt
            if self.v_lat > max_speed_left:
                self.v_lat = max_speed_left
                self.cut_off_flag = True
            if self.v_lat < max_speed_right:
                self.v_lat = max_speed_right
                self.cut_off_flag = True
            
            # check for max lateral speed
            self.omega_max = min(self.omega_max, (0.1+0.1*self.getSpeed()))
            if self.v_lat > self.omega_max:
                self.v_lat = self.omega_max
                self.cut_off_flag = True
            if self.v_lat < -self.omega_max:
                self.v_lat = -self.omega_max
                self.cut_off_flag = True            
            
            self.hyp_angle = self.v_lat / self.speed
            
            if self.unique_id==check_cyclist_id: print("Max_speed_left={}, max_speed_right={}".format(round(max_speed_left,2), round(max_speed_right,2)))
            if self.unique_id==check_cyclist_id: print("Cat. 1 present, v_lat={}".format(round(self.v_lat,2)))
            
            
            ''' Find the leader '''
            # find the leader
            self.findCat12() # get slower cyclists in front
            potential_leaders = []
            self.leader = 0
            if len(self.cat12_cyclists)==0: # if there is no leader
                self.leader = 0
            else: # if there are leader(s)
                # subtract obstructing cyclists from potential leaders
                del_from_pot_lead = []
                for i in obstr_cyclists:
                    del_from_pot_lead.append(i[0])
                if self.unique_id==check_cyclist_id: print("Obstr_cyclists: ", [i.unique_id for i in del_from_pot_lead])
                if self.cut_off_flag == False:
                    potential_leaders = list(set(self.cat12_cyclists) - set(del_from_pot_lead))
                else:
                    potential_leaders = self.cat12_cyclists
                
                if self.des_lat_pos-self.getPos()[1] >= 0:  # move to the left
                    potential_leaders = [i for i in potential_leaders if i.getPos()[1] >= self.getPos()[1]-(self.width) and i.getPos()[1] <= self.des_lat_pos+(self.width)]
                    if self.getSpeed() > 0.5:
                        potential_leaders = [i for i in potential_leaders if i.getPos()[1] <= (self.getPos()[1]+self.width)+(self.omega_max/self.getSpeed())*(i.getPos()[0]-self.getPos()[0])]
                if self.des_lat_pos-self.getPos()[1] < 0:  # move to the right
                    potential_leaders = [i for i in potential_leaders if i.getPos()[1] <= self.getPos()[1]+(self.width) and i.getPos()[1] >= self.des_lat_pos-(self.width)]
                    if self.getSpeed() > 0.5:
                        potential_leaders = [i for i in potential_leaders if i.getPos()[1] >= (self.getPos()[1]-self.width)-(self.omega_max/self.getSpeed())*(i.getPos()[0]-self.getPos()[0])]
                
                if len(potential_leaders) != 0:
                    # obtain closest of those inside the shape
                    closest_pos = self.getPos()[0]+self.cr_length # start finding closest leader in consideration range
                    for i in potential_leaders: # find the closest potential leader
                        if i.getPos()[0] < closest_pos:
                            self.leader = i
                            closest_pos = i.getPos()[0]
                else:
                    self.leader = 0
            
            if self.unique_id==check_cyclist_id: print("Cut_off_flag={}".format(self.cut_off_flag))
            if self.unique_id==check_cyclist_id and self.leader!=0: print("Direct leader {}".format(self.leader.unique_id))
            if self.unique_id==check_cyclist_id and self.leader==0: print("No direct leader")
            
            ''' Check lateral collision '''
            restr_lat_speed = self.omega_max
            self.findAllLateral() # get all cyclists in the prevention zone
            for i in self.all_lateral:
                if (i.getPos()[1]-self.getPos()[1])*self.v_lat > 0: # on the side of the moving angle
                    if abs(i.getPos()[1]-self.getPos()[1]) - self.sr_width > 0: # lateral gap between safety region and lateral cyclist > 0
                        restr_lat_speed = (abs(i.getPos()[1]-self.getPos()[1]) - self.sr_width) / dt
                        if self.v_lat > 0 and self.v_lat > restr_lat_speed:
                            self.restr_lat_speed = restr_lat_speed
                        elif self.v_lat < 0 and self.v_lat < (-1) * restr_lat_speed:
                            self.restr_lat_speed = (-1) * restr_lat_speed
                        else:
                            pass
                    else:
                        self.restr_lat_speed = 0
                        break
            
            
        ''' LEVEL 3: Acceleration according to NDM '''
        def findAcc(self):
            if self.unique_id==check_cyclist_id: print("\n****** LEVEL 3: ACCELERATION **********")
            # define the ndm parameters and functions
            headway_s = 0
            delta_v = 0
            safety_dist_d = self.sr_length + self.length/2  # longitudinal safety distance for NDM
            acc = 0  # realised acceleration
            dec1 = 0  # realised deceleration 1
            dec2 = 0  # realised deceleration 2
            
            # calculate potential (positive) acceleration
            if self.leader == 0: # if there is no leader
                acc = (self.v0-self.getSpeed())/self.a_des
            
            elif self.leader != 0:  # if there is a leader
                headway_s = self.leader.getPos()[0]-self.getPos()[0]  # headway to leader (between centers of cyclists)
                delta_v = self.getSpeed()-self.leader.getSpeed()  # speed difference to leader
                if headway_s <= safety_dist_d:
                    acc = 0
                else:
                    acc = (self.v0-self.getSpeed())/self.a_des
                
                # calculate first deceleration part: matching the speed of the slower leader
                if delta_v > 0:
                    if headway_s > self.length:
                        dec1 = min((delta_v**2)/(2*(headway_s-self.length)), self.b_max) # necessary deceleration to match speed
                    # handle the case where cyclists are colliding at the beginning of the simulation
                    else: 
                        dec1 = self.b_max
                        
                # calculate second deceleration part: fall back to maintain the desired safety distance
                if delta_v <= 1 and headway_s <= safety_dist_d: 
                    dec2 = self.b_max / ((self.length-safety_dist_d)**2) * ((headway_s-safety_dist_d)**2)
                if self.unique_id==check_cyclist_id: print("delta_v={}, hw_s={}, safety_d={}".format(round(delta_v,2),round(headway_s,2),round(safety_dist_d,2)))
            
            self.acceleration = acc - min(dec1+dec2, self.b_max) # limit total deceleration to b_max
            if self.unique_id==check_cyclist_id: print("acc={}, dec1={}, dec2={}".format(round(acc,2),round(dec1,2),round(dec2,2)))
            if self.unique_id==check_cyclist_id: print("Total acceleration={}".format(round(self.acceleration,2)))
        
        ''' 
        **********************************
        *** STEP AND ADVANCE FUNCTIONS ***
        **********************************
        '''
        
        # Read surroundings and determine next coordinates after they all take actions (Note that the agent hasn't really moved when this function is called)
        def step(self):
            ''' CALL LEVEL FUNCTIONS '''                
            if self.unique_id==check_cyclist_id: print("active\n(v0={}, p={})".format(round(self.v0,2),round(self.p,2)))
            self.findLatPos() # level 1: lateral position
            self.findTraj() # level 2: moving angle and leader
            self.findAcc() # level 3: accelerations
            
            ''' CALL UPDATE FUNCTIONS '''
            self.calLatSpeed()
            self.calPos()
            self.calSpeed()
            self.updateCR()
            self.updateSR()
        
            if self.unique_id==check_cyclist_id: print("\n****** UPDATED VALUES *****************")
            if self.unique_id==check_cyclist_id: print("v={}, cr_length={}, sr_length={}".format(round(self.speed,2),round(self.cr_length,2),round(self.sr_length,2)))
            
        # Take (physical) actions, this function would be called automatically after the step() function
        def advance(self):
            self.model.space.move_agent(self,self.next_coords) # update on the canvas
            self.pos = (self.next_coords[0],self.next_coords[1]) # update self attributes
            self.speed = self.next_speed
            self.v_lat_prev = self.v_lat
            self.omega_max = omega_max
            self.cut_off_flag = False
            # clear bicycles which finish the trip
            if self.pos[0] >= 300:
                self.model.to_be_removed.append(self)
    
    #%% Model class
    
    class BikeLane(Model):
        def __init__(self):
            super().__init__()
            self.schedule = SimultaneousActivation(self)
            
            self.space = ContinuousSpace(300.1, path_width, torus=True) # Changed the torus=False here: otherwise, there will be an error because agents are 'out of bounds'
            
            # Initialize model variables
            self.time_step = 0
            self.inflow_count = 0 # The number of bicycle in the vertical queue that will enter
            self.n_agents = 0  # Current number of agents (bicycles) on the entire bike lane
            self.initial_coords = (0,1)
            self.to_be_removed = [] # A list storing bicycles which finish the trip at the time step and to be removed
            
            self.num_all_decision = 0
            self.num_decision = 0 # counters for overtaking decisions
            self.sum_lat_dist = 0 # sum of lateral distance
            
            # Add virtual bicycles for the optional bottleneck
            if bottleneck_width in [1.0,1.5,2.0]:
                print("Bottleneck is active with {} m".format(bottleneck_width))
                # add virtual bicycles at defined positions depending on bottleneck positions
                virt_positions = []
                if bottleneck_width == 1.0:
                    # 4 cyclists
                    virt_positions = [[254,2.4-(4-path_width)], [253,2.8-(4-path_width)], [252,3.2-(4-path_width)], [251,3.6-(4-path_width)]]
                elif bottleneck_width == 1.5:
                    # 3 cyclists
                    virt_positions = [[253,2.9-(4-path_width)], [252,3.3-(4-path_width)], [251,3.7-(4-path_width)]]
                else:
                    # 2 cyclists
                    virt_positions = [[252,3.4-(4-path_width)], [251,3.8-(4-path_width)]]
                    
                for i in range(len(virt_positions)):
                    b = Bicycle('virtual_bn_{}'.format(i), self)
                    b_pos = (virt_positions[i][0], virt_positions[i][1])
                    self.schedule.add(b)
                    self.space.place_agent(b, b_pos)    
                    
            # Data collection functions, collect positions of every bicycle at every step, namely trajectories
            self.datacollector = DataCollector(agent_reporters={"Position": "pos", "Speed": "speed", "latSpeed": "v_lat", "ID": "unique_id", "desSpeed": "v0", "srLength": "sr_length", "srWidth": "sr_width", "crLength": "cr_length"})  # , "leaderDetails": "leader_details"
        
        def deduct(self):
            self.n_agents = self.n_agents - 1
        
        def step(self):
            # Execute agents' functions, including both step and advance
            self.schedule.step()
            # Remove out of bound agents
            for b in self.to_be_removed:
                #print("Remove Bicycle ",b.unique_id)
                self.schedule.remove(b)
                self.space.remove_agent(b)
            self.deduct() # reduce n_agents by 1
            self.to_be_removed = []
            
            # Add bicycle agents at certain time steps
            if self.inflow_count < len(inflow_step):
                if self.time_step == inflow_step[self.inflow_count]:
                    b = Bicycle(self.inflow_count, self)
                    self.schedule.add(b)
                    self.space.place_agent(b, (0,0.5+(random.random()*(path_width-1)))) # self.initial_coords
                    self.inflow_count += 1
                    self.n_agents += 1
            # Update the time
            self.time_step += 1
            print("\n\n\nStep {}, cyclist {}".format(self.time_step,check_cyclist_id))  # review steps in console
            # Execute data collector
            self.datacollector.collect(self)
    
    
    '''
    ***********************
    *** RUN MODEL STEPS ***
    ***********************
    '''
    
    model = BikeLane()
    for i in range(time_steps):  # simulation time steps
        model.step()
    print('-------------------------------------------')
    print('num_decision: ',model.num_all_decision)
    print('num_overtake: ',model.num_decision)
    print('avg_overtake: ',model.num_decision/model.num_all_decision)
    print('sum_lat_dist: ',model.sum_lat_dist)
    print('avg_lat_dist: ',model.sum_lat_dist/model.num_decision)
    print('-------------------------------------------')
    
    agent_pos = model.datacollector.get_agent_vars_dataframe()
    agent_pos = agent_pos.reset_index(level=[0,1]) # reset index to make column callable
    agent_pos['Position'] = agent_pos['Position'].apply(lambda pos: list(pos))
    agent_pos[['Position_x', 'Position_y']] = pd.DataFrame(agent_pos['Position'].tolist(), index=agent_pos.index)
    if type(data_filename) is str:
        agent_pos.to_csv("data/" + data_filename + datetime.now().strftime("_%Y-%m-%d_%H%M") + ".csv", sep=';')
        
    return agent_pos