# -*- coding: utf-8 -*-

from datetime import datetime
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
from matplotlib.animation import PillowWriter
import mpl_toolkits.axes_grid1
import matplotlib.widgets
from matplotlib.patches import Rectangle
from matplotlib.patches import Polygon


class Player(FuncAnimation):  # Player class from https://stackoverflow.com/questions/44985966/managing-dynamic-plotting-in-matplotlib-animation-module/44989063#44989063
    def __init__(self, fig, func, frames=None, init_func=None, fargs=None,
                 save_count=False, mini=0, maxi=18000, pos=(0.04, 0.02), **kwargs):
        self.i = 0
        self.min=mini
        self.max=maxi
        self.runs = True
        self.forwards = True
        self.fig = fig
        self.func = func
        self.setup(pos)
        FuncAnimation.__init__(self,self.fig, self.update, frames=self.play(), 
                                           init_func=init_func, fargs=fargs,
                                           save_count=save_count, **kwargs )    

    def play(self):
        while self.runs:
            self.i = self.i+self.forwards-(not self.forwards)
            if self.i > self.min and self.i < self.max:
                yield self.i
            else:
                self.stop()
                yield self.i

    def start(self):
        self.runs=True
        self.event_source.start()

    def stop(self, event=None):
        self.runs = False
        self.event_source.stop()

    def forward(self, event=None):
        self.forwards = True
        self.start()
    def backward(self, event=None):
        self.forwards = False
        self.start()
    def oneforward(self, event=None):
        self.forwards = True
        self.onestep()
    def onebackward(self, event=None):
        self.forwards = False
        self.onestep()

    def onestep(self):
        if self.i > self.min and self.i < self.max:
            self.i = self.i+self.forwards-(not self.forwards)
        elif self.i == self.min and self.forwards:
            self.i+=1
        elif self.i == self.max and not self.forwards:
            self.i-=1
        self.func(self.i)
        self.slider.set_val(self.i)
        self.fig.canvas.draw_idle()

    def setup(self, pos):
        playerax = self.fig.add_axes([pos[0],pos[1], 0.35, 0.06])
        divider = mpl_toolkits.axes_grid1.make_axes_locatable(playerax)
        bax = divider.append_axes("right", size="80%", pad=0.1)
        sax = divider.append_axes("right", size="80%", pad=0.1)
        fax = divider.append_axes("right", size="80%", pad=0.1)
        ofax = divider.append_axes("right", size="100%", pad=0.1)
        sliderax = divider.append_axes("right", size="1000%", pad=0.3)
        self.button_oneback = matplotlib.widgets.Button(playerax, label='$\u29CF$')
        self.button_back = matplotlib.widgets.Button(bax, label='$\u25C0$')
        self.button_stop = matplotlib.widgets.Button(sax, label='$\u25A0$')
        self.button_forward = matplotlib.widgets.Button(fax, label='$\u25B6$')
        self.button_oneforward = matplotlib.widgets.Button(ofax, label='$\u29D0$')
        self.button_oneback.on_clicked(self.onebackward)
        self.button_back.on_clicked(self.backward)
        self.button_stop.on_clicked(self.stop)
        self.button_forward.on_clicked(self.forward)
        self.button_oneforward.on_clicked(self.oneforward)
        self.slider = matplotlib.widgets.Slider(sliderax, '', 
                                                self.min, self.max, valinit=self.i)
        self.slider.on_changed(self.set_pos)

    def set_pos(self,i):
        self.i = int(self.slider.val)
        self.func(self.i)

    def update(self,i):
        self.slider.set_val(i)


def plot_simulation(agent_pos, 
                    dt = 0.5, 
                    path_width = 2,
                    bottleneck_width = 0,
                    anim_interval = 500, # time to update (ms); 200 ms = 5 FPS
                    plot_length = [0,300],  # start and end of space to show the simulation (m)
                    check_cyclist_id = -1,
                    animation_filename = "animation"
                    ): 
            
    # create figure
    fig, ax = plt.subplots(figsize=(20,3), layout='constrained')
    
    # animation function
    def animate(frame):
        
        # clear canvas
        ax.clear()
        
        # set the boundaries of the plot
        ax.set_xlim([plot_length[0],plot_length[1]])
        ax.set_ylim([0,path_width+1])
        # rename the y-tick labels
        # ax.set_yticks([0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5, 4], [-0.5, 0, 0.5, 1, 1.5, 2, 2.5, 3, 3.5])
        # draw the edges of the cycle path
        # ax.plot([0,300], [0.5,0.5], color='grey', zorder=1)
        # ax.plot([0,300], [3.5,3.5], color='grey', zorder=1)
        ax.add_patch(Rectangle((0, 0.5), 300, path_width, color='silver', zorder=1))
        # draw the keep-right position p
        # ax.plot([0,300], [0.8,0.8], color='khaki', zorder=1)
        # ax.plot([0,300], [1.2,1.2], color='khaki', zorder=1)
        ax.add_patch(Rectangle((0, 0.8), 300, 0.4, color='silver', zorder=2))
        
        
        # obtain agents visible in the current simulation step
        agent_pos_frame = agent_pos[agent_pos['Step'] == frame]
        # obtain their position
        x_pos = agent_pos_frame['Position_x']
        y_pos = agent_pos_frame['Position_y']
        cur_speed = agent_pos_frame['Speed']
        cur_lat_speed = agent_pos_frame['latSpeed']
        
        # plot centers of cyclists in the simulation step
        ax.scatter(x_pos, y_pos, color='black', zorder=3)
        for index, row in agent_pos_frame.iterrows():
            if row['ID']==check_cyclist_id:
                ax.scatter(row['Position_x'], row['Position_y'], color='darkred', zorder=5)  # the one cyclist to check has a red dot
                
                ax.plot([row['Position_x'],row['Position_x']+row['srLength'],row['Position_x']+row['srLength'],row['Position_x']],[row['Position_y']+row['srWidth'],row['Position_y']+row['srWidth'],row['Position_y']-row['srWidth'],row['Position_y']-row['srWidth']], color='red', linestyle='dashed', zorder=5)
                
                ax.plot([row['Position_x']-1,row['Position_x'],row['Position_x']+1,row['Position_x'],row['Position_x']-1], [row['Position_y'],row['Position_y']+0.4,row['Position_y'],row['Position_y']-0.4,row['Position_y']], color='red', zorder=5)
                
                ax.plot([row['Position_x'],row['Position_x']+row['Speed']*dt], [row['Position_y'],row['Position_y']+row['latSpeed']*dt], color='darkred', zorder=5)
                
                ax.text(row['Position_x'], row['Position_y']+0.5, "{}/{}".format(round(row['Speed'],1),round(row['desSpeed'],1)), ha='center', va='bottom', color='red', zorder=5)
                ax.text(row['Position_x'], row['Position_y']-0.5, row['ID'], ha='center', va='top', fontsize='large', color='red', zorder=5)
                
                ax.plot([row['Position_x']+row['crLength'],row['Position_x']+row['crLength']], [0,20], color='red', linestyle='dotted')
        
                # ax.scatter(row['leaderDetails'][1][0], row['leaderDetails'][1][1], color='blue', zorder=6)
        # plot diamond shaped size of cyclists
        ax.plot([x_pos-1,x_pos,x_pos+1,x_pos,x_pos-1], [y_pos,y_pos+0.4,y_pos,y_pos-0.4,y_pos], color='grey', zorder=3)
        # plot arrow to next position
        # print(f'\n{x_pos}, {y_pos} -> {x_nextpos}, {y_nextpos}')
        # ax.plot([x_pos,x_nextpos], [y_pos,y_nextpos], color='crimson', zorder=4)
        ax.plot([x_pos,x_pos+cur_speed*dt], [y_pos,y_pos+cur_lat_speed*dt], color='black', zorder=4)
        # ax.arrow(x_pos, y_pos, cur_speed*run.dt, cur_lat_speed*run.dt, color='crimson', zorder=4)
        
        for index, row in agent_pos_frame.iterrows():
            ax.text(row['Position_x'], row['Position_y']+0.5, "{}/{}".format(round(row['Speed'],1),round(row['desSpeed'],1)), ha='center', va='bottom')
            ax.text(row['Position_x'], row['Position_y']-0.5, row['ID'], ha='center', va='top', fontsize='large')
        
        # get minutes and seconds from the simulation step
        minutes = int(frame/(60/dt))
        seconds = round((frame % (60/dt)) * dt, 2)
        hundredth = int(round((seconds % 1) * 100, 0))
        seconds = int(seconds)
        
        # naming the plot
        ax.set_title(f'Time {minutes:02}:{seconds:02}.{hundredth:02}  |  Step {frame:04}  |  dt = {dt}  |  {datetime.now().strftime("%Y-%m-%d %H:%M")} ')
        ax.set_xlabel('Cycle path length (m)')
        ax.set_ylabel('Cycle path width (m)')
        
        for t in ax.texts:
            t.set_clip_on(True)
        
        # bottleneck
        if bottleneck_width in [1.0,1.5,2.0]:
            coords = []
            if bottleneck_width == 1.0:
                # 4 cyclists
                # virt_positions = [[254,2.4], [253,2.8], [252,3.2], [251,3.6]]
                coords = [(249,4.0-(3-path_width)),(255.25,1.5-(3-path_width)),(300,1.5-(3-path_width)),(300,4.0-(3-path_width))]
            elif bottleneck_width == 1.5:
                # 3 cyclists
                # virt_positions = [[253,2.9], [252,3.3], [251,3.7]]
                coords = [(249,4.1-(3-path_width)),(254.25,2.0-(3-path_width)),(300,2.0-(3-path_width)),(300,4.1-(3-path_width))]
            else:
                # 2 cyclists
                # virt_positions = [[252,3.4], [251,3.8]]
                coords = [(249,4.3-1),(253.25,2.6-1),(300,2.6-1),(300,4.3-1)]
            ax.add_patch(Polygon(coords, color='white', zorder=1.2))
        
    # matplotlib animation function
    anim = Player(fig, animate, agent_pos['Step'].unique(), interval=anim_interval, cache_frame_data=True)
    fig.show()
    
    
    # WRITING OF THE GIF FILE IS SOMEHOW CORRUPTED
    '''
    # save animation as gif into current directory
    if type(animation_filename) is str:
        writer = PillowWriter(fps=(1000/anim_interval), metadata=dict(artist='Me'), bitrate=1000)
        anim.save("figures/" + animation_filename + datetime.now().strftime("_%Y-%m-%d_%H%M") + ".gif", writer=writer)
    '''
