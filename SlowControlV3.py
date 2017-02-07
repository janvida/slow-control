#Derrick Kress
#Jan 20 2010
#SlowControlV2.py

#!/usr/bin/python2.6

import wx
import os
import serial
import time
import datetime

#Define default serialcom settings
BAUD='9600'
Port1='/dev/ttyM0'
Port2='/dev/ttyM1'
Port3='/dev/ttyM2'
Port4='/dev/ttyM3'
Port5='/dev/ttyM4'
Port6='/dev/ttyM5'
Port7='/dev/ttyM6'
Port8='/dev/ttyM7'

#Global string for storing open ports
strs = 8 * [None]
str1=None
str2=None
str3=None
str4=None
str5=None
str6=None
str7=None
str8=None

#conversion factor for Battery monitor
convert_battery=19.9336607769e-3
#Conversion factor for High Voltage
convert_HV=1.25*996.015936255e-3
#Conversion factor for Temperature
#directly for v-divider on pcb,to milivolts, to kelvin (10mV per degree kelvin)
convert_temp=(((10+4.66)/4.66)*1e-3/10e-3)
#Conversion factor for Anode voltage
convert_anode=1.78850467238e-3

#Ending NULL character sent by comm ports
NULL='\r'
#Default HV output
HV_default=1000
#Default timer divisor (1 sec) used for ping timing
Time=1000

#Panel Background color
PBcolor='white'
#Button background color
BNcolor=''
#Button enable color
BEcolor='green'

#Global for start/stop of recording
record=0
#Global for opening serial ports for communication
OpenPorts=0
#Global to detect if currently recording
recording=0
#Global for clock update, wait if button is pressed
Clk=0
#Global for starting ping
start=0
#Global fout
fout=None
#Global values for board number identification (defalt 4)
BrdNum=4
#global values for all device boards (possible 8 max boards to be used)
adc0=0
adc1=0
adc2=0
adc3=0



# Get the number of boards and store in as a global variable BrdNum
class GetBrdNum(wx.Dialog):
    def __init__(self, parent, id):
        wx.Dialog.__init__(self, parent, id,size=(220, 110))

        box=wx.StaticBox(self, -1, '', (5, 5), size=(210, 100))
        wx.StaticText(self, -1, 'Enter the number of devices:', (15, 25))
        self.sc1=wx.SpinCtrl(self, -1, '4', (25, 60), (60, -1), min=1, max=8)
        ok=wx.Button(self, 1, 'Ok', (115, 60), (60, -1))
        self.Bind(wx.EVT_BUTTON, self.OnClose, id=1)
        self.Centre()
        self.ShowModal()
        self.Destroy()

    def OnClose(self, event):
        global BrdNum
        BrdNum=self.sc1.GetValue()
        self.Close()





# Get the timeout values for pinging boards
class GetPing(wx.Dialog):
    def __init__(self, parent, id):
        wx.Dialog.__init__(self, parent, id,size=(200, 110))

        box=wx.StaticBox(self, -1, '', (5, 5), size=(190, 100))
        wx.StaticText(self, -1, 'Enter ping time is seconds:', (15, 25))
        self.sc1=wx.SpinCtrl(self, -1, '1', (25, 60), (60, -1), min=1, max=60)
        ok=wx.Button(self, 1, 'Ok', (115, 60), (60, -1))
        self.Bind(wx.EVT_BUTTON, self.OnClose, id=1)
        self.Centre()
        self.ShowModal()
        self.Destroy()

    def OnClose(self, event):
        global Time
        Time=int(self.sc1.GetValue())*1000
        self.GetParent().timer.Start(Time)
        self.Destroy()


# Get the timeout values for pinging boards
class GetPorts(wx.Dialog):
    def __init__(self, parent, id):
        wx.Dialog.__init__(self, parent, id,size=(200, 110))

        box=wx.StaticBox(self, -1, '', (5, 5), size=(190, 100))
        wx.StaticText(self, -1, 'Enter ping time is seconds:', (15, 25))
        self.sc1=wx.SpinCtrl(self, -1, '1', (25, 60), (60, -1), min=1, max=60)
        ok=wx.Button(self, 1, 'Ok', (115, 60), (60, -1))
        self.Bind(wx.EVT_BUTTON, self.OnClose, id=1)
        self.Centre()
        self.ShowModal()
        self.Destroy()


################################################################################
#   -MainControl-                                                              #
#Create panel for MainControl. This will give control for                      #
#turning on the recording of data as well as reseting the system and           #
#connecting to the SlowControl boards.                                         #
################################################################################
class MainControl(wx.Panel):
    def __init__(self, parent, id):
        wx.Panel.__init__(self, parent, id, style=wx.BORDER_SUNKEN)
        self.SetBackgroundColour(PBcolor)
     
        #Set sizer for button display
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        vbox = wx.BoxSizer(wx.VERTICAL)
       
        #Close button
        self.button1=wx.Button(self,-1,label="RECORD",size=(-1,-1))
        #Reset button
        self.button2=wx.Button(self,label="END",size=(-1,-1))
        #START button
        self.button3=wx.Button(self,label="CONNECT",size=(-1,-1))
        #STOP button
        self.button4=wx.Button(self,label="STOP",size=(-1,-1))
	#Reset button
        self.button5=wx.Button(self,label="RESET",size=(-1,-1))	
	#Exit button
        self.button6=wx.Button(self,-1,label="EXIT",size=(-1,-1))
        
        #Add to vboxBoxSizer
        vbox.Add(self.button1,0, wx.ALIGN_CENTER | wx.EXPAND |wx.LEFT | wx.RIGHT,5 )
        vbox.Add(self.button2,0, wx.ALIGN_CENTER | wx.EXPAND |wx.LEFT | wx.RIGHT,5 )
        vbox.Add(self.button3,0, wx.ALIGN_CENTER | wx.EXPAND |wx.LEFT | wx.RIGHT,5 ) 
        vbox.Add(self.button4,0, wx.ALIGN_CENTER | wx.EXPAND |wx.LEFT | wx.RIGHT,5 )
        vbox.Add(self.button5,0, wx.ALIGN_CENTER | wx.EXPAND |wx.LEFT | wx.RIGHT,5 ) 
        vbox.Add(self.button6,0, wx.ALIGN_CENTER | wx.EXPAND |wx.LEFT | wx.RIGHT,5 )
        
        hbox.Add(vbox,1,wx.ALIGN_CENTER)
        self.SetSizer(hbox)
      
        #Bind button press(EVENTS) to funtions
        self.Bind(wx.EVT_BUTTON, self.Record,id=self.button1.GetId())
        self.button1.SetBackgroundColour(BNcolor)
        self.Bind(wx.EVT_BUTTON, self.End, id=self.button2.GetId())
        self.button2.SetBackgroundColour(BNcolor)
        self.Bind(wx.EVT_BUTTON, self.Start, id=self.button3.GetId())
        self.button3.SetBackgroundColour(BNcolor)
        self.Bind(wx.EVT_BUTTON, self.Stop, id=self.button4.GetId())
        self.button4.SetBackgroundColour(BNcolor)
	self.Bind(wx.EVT_BUTTON, self.resetBRDS, id=self.button5.GetId())
        self.button5.SetBackgroundColour(BNcolor)
	self.Bind(wx.EVT_BUTTON, self.OnExit, id=self.button6.GetId())
        self.button6.SetBackgroundColour(BNcolor)

	#Bind entering into button space to functions, used to display button funtion
        self.Bind(wx.EVT_ENTER_WINDOW, self.Record_S,id=self.button1.GetId())               
        self.Bind(wx.EVT_ENTER_WINDOW, self.End_S, id=self.button2.GetId())
        self.Bind(wx.EVT_ENTER_WINDOW, self.Start_S, id=self.button3.GetId())
        self.Bind(wx.EVT_ENTER_WINDOW, self.Stop_S, id=self.button4.GetId())
        self.Bind(wx.EVT_ENTER_WINDOW, self.resetBRDS_S, id=self.button5.GetId())
        self.Bind(wx.EVT_ENTER_WINDOW, self.OnExit_S, id=self.button6.GetId())


    #Funtions for displaying button functions
    def Record_S(self,event):
        self.GetParent().GetParent().SetStatusText(" Connected to device(s)")
    def End_S(self,event):
        self.GetParent().GetParent().SetStatusText(" Connected to device(s)")
    def Start_S(self,event):
        self.GetParent().GetParent().SetStatusText(" Connected to device(s)")
    def Stop_S(self,event):    
        self.GetParent().GetParent().SetStatusText(" Connected to device(s)")
    def resetBRDS_S(self,event):
        self.GetParent().GetParent().SetStatusText(" Connected to device(s)")
    def OnExit_S(self,event):
        self.GetParent().GetParent().SetStatusText(" Connected to device(s)")        

    #Begin Pinging, set start to 1 and Clk to 2. When start is 1, in MainWindow the communication
    #between computer and board begins, status is shown in statusbar.   
    def Start(self,event):
	#Set global Clk to 2, this will display the status for 2 seconds
        global Clk
        Clk = 2
        now = datetime.datetime.now()
	now=now.strftime("%H:%M:%S")
	self.GetParent().GetParent().SetStatusText(now+" Connected to device(s)")
	#Set comunicatin variable 'start' to true or 1.  MainWinow uses this in the time funtion
        global start
        start=1
	#Set serial global variable to 1, this opens ports for all boards, does not repeat during 
	#subsequent pinging
	global OpenPorts	
	OpenPorts=1	
        #Change button color
        obj =  event.GetEventObject()
        obj.SetBackgroundColour(BEcolor)
        obj.Refresh()
	

        
    #Stop Pinging, set start to 0, pinging loop is skipped in MainWindow
    def Stop(self,event):
        #Set global Clk to 2, this will display the status for 2 seconds
        global Clk
        Clk = 2
        now = datetime.datetime.now()
	now=now.strftime("%H:%M:%S")
	self.GetParent().GetParent().SetStatusText(now+" Disconnected from boards")
	#Set comunicatin variable 'start' to false or 0
        global start
        start=0
	#Turn serial variabl to 0
	global OpenPorts
	OpenPorts=0
	#Change button color
        self.button3.SetBackgroundColour(BNcolor)#Reset button
        

    #Reset all BRDS by switching com ports.    
    def resetBRDS(self,event):
	#Set global Clk to 2, this will display the status for 2 seconds
        global Clk
        Clk = 2
        now = datetime.datetime.now()
	now=now.strftime("%H:%M:%S")
	self.GetParent().GetParent().SetStatusText(now+" SlowControl system reset ")	
	global BrdNum        
	count=1	    
        while count <= BrdNum:
		#Dynamicaly assign PORT to the current board device location
		#Device locations are found at top, or in settings		
		exec 'PORT = Port%s' % count               
		exec 'self.GetParent().GetParent().panel%s.HV_on.SetBackgroundColour(BNcolor)' % count		
		if os.path.exists(PORT):
                    #Begin pinging individual boards as defined by PORT
                    #Write reset command to board       
                    ser = serial.Serial(PORT, BAUD, timeout=1)                
                    ser.write("DAC0"+NULL)
                    ser.readline()
                    ser.write("RES"+NULL)
		count=count+1
	


    #Turn HV OFF for all BRDS via com ports.    
    def Record(self,event):
	#Set global Clk to 2, this will display the status for 2 seconds
        global Clk
        Clk = 2
        now = datetime.datetime.now()
	now=now.strftime("%H:%M:%S")
	self.GetParent().GetParent().SetStatusText(now+" Recording enabled")
        #Set global in charge of starting record
        global record
        record = 1
        #Set global for knowing if a recording is taking place, 1 is not recording
        global recording
        recording = 1
	#Change button color
        obj =  event.GetEventObject()
        obj.SetBackgroundColour(BEcolor)
        obj.Refresh()
            
    #Turn HV ON for all BRDS via com ports.    
    def End(self,event):
	#Set global Clk to 2, this will display the status for 2 seconds
        global Clk
        Clk = 2
	now = datetime.datetime.now()
	now=now.strftime("%H:%M:%S")
	self.GetParent().GetParent().SetStatusText(now+" Recording disabled")
	#close fout file, global
	global record	
	if record ==1:
		fout.close()        
	#Set global in charge of stopping record
        record = 0
        #Set global to signal that a recording is not in progress
        global recording
        recording = 0
	self.button1.SetBackgroundColour(BNcolor)#Reset button

    #Prompt before final exit.
    def OnExit(self, event):
	#Send OnExit event to MainWindow
	event.Skip()



################################################################################ 
#   -Data-                                                                     #
#Data sets up the GUI display for the East telescope SlowControl Boards.       #
#The panel is arranged with BoxSizers and GridSizers and also contains         #
#a spinner for explicitly setting the voltage output on the EMCO high          #
#voltage power supply.                                                         #
################################################################################
class Data(wx.Panel):
    def __init__(self, parent, id):
        wx.Panel.__init__(self, parent, id, style=wx.BORDER_SUNKEN)
        #Use global variables
        global count

        self.SetBackgroundColour(PBcolor)
                       
        #Set sizer for panel
        vbox_top = wx.BoxSizer(wx.VERTICAL)
        
        #Header, info and voltage display
        title=wx.StaticText(self, -1, 'Board '+str(count))
        divider=wx.StaticLine(self, -1, (25, 50), (50,1))
        
        #Create text strings for displaying SlowControl data grid 1
        #This is what will change when text is updated
        self.textadc1=wx.StaticText(self, -1, '     '+str(adc1)+' C')
	self.textadc0=wx.StaticText(self, -1, '     '+str(adc0)+' V')
        self.textadc3=wx.StaticText(self, -1, '     '+str(adc3)+' V')
        self.textadc2=wx.StaticText(self, -1, '     '+str(adc2)+' V')

        #Create grid1 grouping display
        grid1 = wx.GridSizer(2, 2, 1,1)
        grid1.Add(wx.StaticText(self, -1, 'TMP'))
        grid1.Add(self.textadc1)
        grid1.Add(wx.StaticText(self, -1, 'HVM'))
        grid1.Add(self.textadc0)
        grid1.Add(wx.StaticText(self, -1, 'AND'))
        grid1.Add(self.textadc3)
        grid1.Add(wx.StaticText(self, -1, 'BAT'))
        grid1.Add(self.textadc2)
        
	#Create vertical sizer for grid1 to belong to
	hbox=wx.BoxSizer(wx.HORIZONTAL)
	#Add grid 1 to hbox
	hbox.Add(grid1,1)	
	
        #Create SpinCtrl for controling HV
        self.sc1 = wx.SpinCtrl(self, -1, '',  (-1, -1), (-1, -1))
        self.sc1.SetRange(0, 1250)
        self.sc1.SetValue(HV_default)
       
        #Create buttons for EMCO HV update
        self.update=wx.Button(self,-1,label="SET HV",size=(-1,-1))
	self.update.SetBackgroundColour(BNcolor)        
	self.Bind(wx.EVT_BUTTON, self.HVupdate,id=self.update.GetId())
        
        #Create sizer for HVon and HVoff buttons
        HV_buttons = wx.BoxSizer(wx.HORIZONTAL)
        self.HV_on=wx.Button(self,-1,label="ON",size=(-1,-1))
        self.HV_on.SetBackgroundColour(BNcolor)
        self.HV_off=wx.Button(self,-1,label="OFF",size=(-1,-1))
        self.HV_off.SetBackgroundColour(BNcolor)
        HV_buttons.Add(self.HV_on,1,wx.EXPAND)
        HV_buttons.Add(self.HV_off,1,wx.EXPAND)
        
	#Create bindings for panel buttons
	self.Bind(wx.EVT_BUTTON, self.HVon,id=self.HV_on.GetId())
	self.Bind(wx.EVT_BUTTON, self.HVoff,id=self.HV_off.GetId())
	
        #Finalize box and show
        vbox_top.Add(title,0, wx.ALIGN_CENTER | wx.TOP,5)
        vbox_top.Add(divider,0,wx.ALIGN_CENTER)
        vbox_top.Add(hbox,1,wx.ALIGN_CENTER)
        vbox_top.Add(self.sc1,0,wx.ALIGN_CENTER | wx.EXPAND | wx.LEFT | wx.RIGHT,5)
        vbox_top.Add(self.update,0,wx.ALIGN_CENTER | wx.EXPAND | wx.LEFT | wx.RIGHT ,5)
        vbox_top.Add(HV_buttons,0,wx.ALIGN_CENTER | wx.EXPAND | wx.LEFT | wx.RIGHT | wx.BOTTOM,5)
        self.SetSizer(vbox_top)


    #On HVupdate send command to update DAC output on SlowControl board.
    def HVupdate(self,event):
	count=1
	while count <= BrdNum:
		exec "tmp=bool(self.GetId()==self.GetParent().GetParent().panel%s.GetId())" % count
		if tmp==True:
			exec 'PORT = Port%s' % count
			if os.path.exists(PORT):
				#Get value stored in spinner update
				exec 'EMCO = 2*self.GetParent().GetParent().panel%s.sc1.GetValue()' % count				
				#Send on command to the board referenced by count (board#)
				ser = serial.Serial(PORT, BAUD, timeout=1)
				ser.write("DAC"+str(EMCO)+NULL)
				ser.readline()
				ser.close()
		count=count+1
        

    def HVon(self,event):
	obj =  event.GetEventObject()
        obj.SetBackgroundColour(BEcolor)
        obj.Refresh()
	#Turn on 'connect' so as to be alert of whats happening in the system
	global start
	if start==0:
		now = datetime.datetime.now()
		now=now.strftime("%H:%M:%S")		
		self.GetParent().GetParent().SetStatusText(now+" Connected to device(s)")	
	start = 1	
	self.GetParent().GetParent().maincontrol.button3.SetBackgroundColour(BEcolor)
	count=1
	while count <= BrdNum:
		exec "tmp=bool(self.GetId()==self.GetParent().GetParent().panel%s.GetId())" % count
		if tmp==True:
			exec 'PORT = Port%s' % count
			if os.path.exists(PORT):
				#Send on command to the board referenced by count (board#)
				ser = serial.Serial(PORT, BAUD, timeout=1)
				ser.write("HV1"+NULL)
				ser.readline()
				#Get value stored in spinner update
				exec 'EMCO = 2*self.GetParent().GetParent().panel%s.sc1.GetValue()' % count				
				#Send on command to the board referenced by count (board#)
				ser = serial.Serial(PORT, BAUD, timeout=1)
				ser.write("DAC"+str(EMCO)+NULL)
				ser.readline()	
				ser.close()
		count=count+1
	

    def HVoff(self,event):
	self.HV_on.SetBackgroundColour(BNcolor)#Reset button
	count=1
	while count <= BrdNum:
		exec "tmp=bool(self.GetId()==self.GetParent().GetParent().panel%s.GetId())" % count
		if tmp==True:
			exec 'PORT = Port%s' % count
			if os.path.exists(PORT):
				#Send on command to the board referenced by count (board#)
				ser = serial.Serial(PORT, BAUD, timeout=1)
				ser.write("HV0"+NULL)
				ser.readline()
				ser.write("DAC0"+NULL)
				ser.readline()
				ser.close()
		count=count+1


	

#GetGlobals is a class that will automatically initialize all globals employed in SlowControl.
#This class is called whenever any global variable needs to be referenced.
class GetGlobals():
	global start
	global BrdNum
	global Port1
	global Port2
	global Port3
	global Port4
	global Port5
	global Port6
	global Port7
	global Port8
#################################################################################################################


class MainWindow(wx.Frame):
    def __init__(self, parent, id, title):
        wx.Frame.__init__(self, parent, id, title)
        #class variable for file open
	fout = None
	global Time
	#Create timer for ping request time, (asking SC boards for data)
        self.OnTimer(None)
        self.timer = wx.Timer(self,-1)
        #Update timer and run OnTimer every interval Time ms
        self.timer.Start(Time)
        self.Bind(wx.EVT_TIMER,self.OnTimer)
	
	#Declare the global variables that will be reverenced in MainWindow        
	global BrdNum
        global count
	
	#Get the number of boards to be used via GetBrdNum class        
	GetBrdNum(None, -1)
     
        # A StatusBar in the bottom of the window
        self.CreateStatusBar() 
        # Setting up the menu, define filemenu and setupmenu.
        filemenu= wx.Menu()
        setupmenu=wx.Menu()
        helpmenu=wx.Menu()
        #wx.ID_ABOUT and wx.ID_EXIT are standard ids provided by wxWidgets.
        menuAbout = filemenu.Append(wx.ID_ABOUT, "&About"," Information about SlowControl")
        filemenu.AppendSeparator()
        menuExit = filemenu.Append(wx.ID_EXIT, "E&xit\tAlt-X", "Close window and exit program.")
        #Other menu items
        #menuSetup = setupmenu.Append(wx.NewId(),"Configure Ports","Modify port settings")
        menuTime = setupmenu.Append(wx.NewId(),"Ping Settings","Modify timing settings")
        menuTutorial = helpmenu.Append(wx.NewId(),"Tutorial","Help with using SlowControl")
        # Creating the menubar.
        menuBar = wx.MenuBar()
	
	menuBar.Append(filemenu,"&File") # Adding the "filemenu" to the MenuBar
        menuBar.Append(setupmenu,"&Setup") # Adding the "filemenu" to the MenuBar
        #menuBar.Append(helpmenu,"&Help") # Adding the "helpmenu" to the MenuBar
        self.SetMenuBar(menuBar)  # Adding the MenuBar to the Frame content.
        # Set events in MainWindow.
        self.Bind(wx.EVT_MENU, self.OnAbout, menuAbout)
        self.Bind(wx.EVT_MENU, self.OnExit, menuExit)
	self.Bind(wx.EVT_MENU, self.OnTime, menuTime)
        self.Show(True)
        
	#Set events in all classes (MainControl)
	self.Bind(wx.EVT_BUTTON, self.OnExit)

        #Create panel to display data & other classes in.
        panel = wx.Panel(self, -1)
        vbox_top = wx.BoxSizer(wx.HORIZONTAL)
        
        #Add MainControl to front panel
	self.maincontrol=MainControl(panel,-1)        
	vbox_top.Add(self.maincontrol,1,wx.EXPAND | wx.ALL,5)
        
        #Logic to appropriate the number of boards chosen
	count = 1        
	while count <= BrdNum:
            #For every Brd a panel 'Data(panel,-1)' will be created
	    #This is done dynamically with the exec command, it will create
	    #self.panel1,self.panel2 etc for the number of boards that 
	    #are to be used.
	    exec 'self.panel%s = Data(panel,-1)' % count
	                   
	    #Add panel to BoxSizer in main window, use the eval
	    #command to evaluate the value of the string, ie
	    #self.panel1, self.panel2, etc.
	    vbox_top.Add(eval('self.panel'+str(count)),1,wx.EXPAND | wx.ALL,5)
            tmp=0
	    count=count+1
        
	#Set the minimum window size to fit BrdNum
        self.SetSizeWH(300+int(140*(BrdNum-1)),250)
                  
        #Initialize box sizer
        panel.SetSizer(vbox_top) 
        #Display frame in window
        self.Center()
        #Show MainWindow
        self.Show(True)
             
             

        #About on menu, explain self.
    def OnAbout(self,event):
        # A message dialog box with an OK button.
        wx.AboutBox()
        
    def OnExit(self, event):
        dlg = wx.MessageDialog(self, 
            "Do you really want to close SlowControl?",
            "Confirm Exit", wx.OK|wx.CANCEL|wx.ICON_QUESTION)
        result = dlg.ShowModal()
        dlg.Destroy()
        if result == wx.ID_OK:
            self.Close()
            self.Destroy()
    
    #Change ping time settings
    def OnTime(self,event):
	GetPing(self,-1)

	  
    def OnTimer(self,event):
        #When the start button is pressed, read from ports every 'timer' event
	#OnTimer also updates the data displayed in all panels
        #Let me use globals please! (needed to see globals)
	#GetGlobals()
	tmp=0
	
        global Clk
        if Clk==0:
            self.SetStatusText(time.ctime())     	
        else:
            Clk = Clk-1

        global start		
	if start==1:
            count=1
	    
            #Let me use record and recording variables for file writing.
            global record
            global recording
            
            #if record global is set to one, record anode signals
            if record==1 & recording==1:
		current = time.localtime(time.time())		
		ts = time.strftime("a%Y%b%d%t", current)
                #open file 'fout' to store variables with tag of time for filename
		global fout                
		fout = open(ts,'w')
                #set recording variable to 1, so file is not recreated each time tick
                recording = 0               
                
		    
            #Dynamicaly assign PORT to the current board device location
	    #Device locations are found at top, or in settings, ports will
            #be opened for each board as 'ser1,ser2,ser3,etc'		
	    tmp=0
	    global OpenPorts
	    global strs
	    while (tmp<BrdNum) & (OpenPorts==1):
		exec 'PORT = Port%s' % str(tmp+1)               
		if os.path.exists(PORT):
								
			strs[tmp] = serial.Serial(PORT, BAUD, timeout=1)
			print 'strs[%s] =' % tmp, strs[tmp]		
					
		else:
			start=0
			error=wx.MessageDialog(None,'Error accessing port on '+str(PORT),'Communication Error',wx.OK|wx.ICON_ERROR)
			error.ShowModal()
			count=BrdNum+1
			self.maincontrol.button3.SetBackgroundColour(BNcolor)      
		#Do not open any more ports after all boards have allocated prts			
		if tmp==int(BrdNum-1):
			OpenPorts=0		
		tmp=tmp+1		

	    #if recording, write time for the beggining of the line
	    if record ==1:
		current = time.localtime(time.time())		
		ts = time.strftime("%H:%M:%S", current)
		fout.write(ts)
            #Cycle through all Brds and get data from each up til count<BrdNum or total boards
            while count <= BrdNum:
		tmp=0
                #Enter loop to get adc0..3 values and store them dynamically
		while tmp<4:
			#Use globas for adc data                        
			GetGlobals()	         
			#write to board '#count'    
			                 
			strs[count-1].write("RDA"+str(tmp)+NULL)			
			#exec 'ser%s.write("RDA"+str(tmp)+NULL)' % count
			strs[count-1].readline()
			                    
			#exec 'ser%s.readline()' % count
						
			exec 'adc%s=strs[count-1].readline()' % tmp
					
			#Update counter			
			tmp=tmp+1
			   
		    
		#This code will update all of the board numbers for each port cycle. It also
		#incorperates the variables for scaling the outputs from the adc on the
		#ATmega168. the if statement checks to see that the input is a valid decimal
		#digit so there is no garbage on the output.	    	
		if adc0.strip().isdigit():			
			#Convert the value input to the right scale, using convert_HV
			tmp=int(int(adc0)*convert_HV)
			exec 'self.panel%s.textadc0.SetLabel("-%s V")' % (count,int(tmp))
		if adc1.strip().isdigit():		    	
			#Convert the value input to the right scale, using convert_temp, K to C -273
			tmp=(int(adc1)*convert_temp-273)
			exec 'self.panel%s.textadc1.SetLabel("%s C")' % (count,int(tmp))
		if adc2.strip().isdigit():	    
			#Convert the value input to the voltage scale, using convert_battery
			tmp='%.2f'%(int(adc2)*convert_battery)	        		
			exec 'self.panel%s.textadc2.SetLabel("%s V")' % (count,str(tmp))
			if record==1:
				fout.write(" "+str(tmp))
		if adc3.strip().isdigit():
			tmp='%.3f'%(int(adc3)*convert_anode)	  	
		    	exec 'self.panel%s.textadc3.SetLabel("%s V")' % (count,str(tmp))
			#If recording enabled, write to file
			if record==1:
				fout.write(" "+str(tmp))
		 
		#Update counter	        
		count=count+1      
	    #Put newline on fout if recording
	    if record ==1:
		fout.write("\n")   
	   
           

app = wx.App()
MainWindow(None, -1, 'SlowControl V1.1')
app.MainLoop()

