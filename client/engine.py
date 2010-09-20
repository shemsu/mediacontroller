from multiprocessing import Process
from sqlite import SQLite

import constants as const
import socket
import wx


class ServerDialog(wx.Frame):
    def __init__(self, parent):
        wx.Frame.__init__(self, parent, -1, title = "Server", size = const.SERVER_DIALOG_SIZE, style = wx.FRAME_FLOAT_ON_PARENT | wx.CAPTION | wx.FRAME_TOOL_WINDOW)
        
        self.panel = wx.Panel(self, -1)
        self.parent = parent
        
        self.label_server = wx.StaticText(self.panel, -1, "Server domain to connect to")
        self.input_server = wx.TextCtrl(self.panel, -1, size = const.SERVER_DIALOG_INPUT_SIZE)
        self.input_server.SetValue(self.parent.storage.GetServer())
        self.button_ok = wx.Button(self.panel, wx.ID_OK, "OK")
        self.button_cancel = wx.Button(self.panel, wx.ID_CANCEL, "Cancel")
        self.button_ok.SetDefault()
        
        self.button_ok.Bind(wx.EVT_BUTTON, self.OnOK)
        self.button_cancel.Bind(wx.EVT_BUTTON, self.OnCancel)
        
        self.SetLayout()
        self.parent.Enable(False)
    
    def SetLayout(self):
        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox_1 = wx.BoxSizer(wx.HORIZONTAL)
        hbox_2 = wx.BoxSizer(wx.HORIZONTAL)
        hbox_3 = wx.BoxSizer(wx.HORIZONTAL)
        
        hbox_1.Add(self.label_server, 0, wx.ALIGN_CENTER | wx.ALL, 2)
        hbox_2.Add(self.input_server, 0, wx.ALIGN_CENTER | wx.ALL, 2)
        hbox_3.Add(self.button_ok, 0, wx.ALIGN_CENTER | wx.ALL, 2)
        hbox_3.Add(self.button_cancel, 0, wx.ALIGN_CENTER | wx.ALL, 2)
        
        vbox.Add(hbox_1, 0, wx.ALIGN_CENTER)
        vbox.Add(hbox_2, 0, wx.ALIGN_CENTER)
        vbox.Add(hbox_3, 0, wx.ALIGN_CENTER)
        
        self.panel.SetSizer(vbox)
        self.Layout()
    
    def Show(self):
        self.CenterOnParent()
        wx.Frame.Show(self)
        self.Raise()
    
    def OnOK(self, event):
        if self.input_server.IsModified():
            server = self.input_server.GetValue()
            if not server is None:
                self.parent.storage.SetServer(server)
                self.parent.server = server
        self.Finalize()
    
    def OnCancel(self, event):
        self.Finalize()
    
    def Finalize(self):
        self.parent.Enable(True)
        self.Destroy()


class TaskBarMenu(wx.Menu):
    def __init__(self, main_form):
        wx.Menu.__init__(self)
        
        self.main_form = main_form
        
        show = wx.MenuItem(self, wx.NewId(), self.main_form.IsShown() and "Hide" or "Show")
        play = wx.MenuItem(self, wx.NewId(), "Play / Pause")
        stop = wx.MenuItem(self, wx.NewId(), "Stop")
        quit = wx.MenuItem(self, wx.NewId(), "Quit")
        self.AppendItem(show)
        self.AppendSeparator()
        self.AppendItem(play)
        self.AppendItem(stop)
        self.AppendSeparator()
        self.AppendItem(quit)
        self.Bind(wx.EVT_MENU, self.OnShow, id = show.GetId())
        self.Bind(wx.EVT_MENU, self.OnPlay, id = play.GetId())
        self.Bind(wx.EVT_MENU, self.OnStop, id = stop.GetId())
        self.Bind(wx.EVT_MENU, self.OnQuit, id = quit.GetId())
    
    def OnShow(self, event):
        self.main_form.ToggleShown()
    
    def OnPlay(self, event):
        self.main_form.Play()
    
    def OnStop(self, event):
        self.main_form.Stop()
    
    def OnQuit(self, event):
        self.main_form.Quit()


class MainFrame(wx.Frame):
    def __init__(self):
        wx.Frame.__init__(self, None, -1, "Media Controller", size = const.MAIN_FRAME_SIZE, style = wx.CAPTION | wx.CLOSE_BOX)
        
        self.panel = wx.Panel(self, -1)
        self.storage = SQLite()
        self.player = self.storage.GetPlayer()
        self.server = self.storage.GetServer()
        self.socket = None
        self.communicator = None
        
        self.SetIcon(wx.Icon(const.LOGO_ICON, wx.BITMAP_TYPE_PNG))
        self.tbicon = wx.TaskBarIcon()
        self.tbicon.SetIcon(wx.Icon(const.TRAY_LOGO_ICON, wx.BITMAP_TYPE_XPM), "Media Controller")
        self.tbicon.Bind(wx.EVT_TASKBAR_RIGHT_DOWN, self.OnTaskBarRight)
        self.tbicon.Bind(wx.EVT_TASKBAR_LEFT_DOWN, self.OnTaskBarLeft)
        
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        
        self.CreateMenuBar()
        self.CreateControls()
        self.SetLayout()
        self.ServerConnect()
    
    def CreateMenuBar(self):
        menu = wx.MenuBar()
        settings = wx.Menu()
        
        player = wx.Menu()
        for item in const.PLAYERS.keys():
            menu_item = wx.MenuItem(player, wx.NewId(), item, kind = wx.ITEM_RADIO)
            player.AppendItem(menu_item)
            if item == self.player:
                menu_item.Check(True)
            self.Bind(wx.EVT_MENU, self.OnPlayerMenu, id = menu_item.GetId())
        
        server = wx.MenuItem(settings, wx.NewId(), "Server")
        quit = wx.MenuItem(settings, wx.NewId(), "Quit")
        
        settings.AppendMenu(wx.NewId(), "Player", player)
        settings.AppendItem(server)
        settings.AppendSeparator()
        settings.AppendItem(quit)
        
        self.Bind(wx.EVT_MENU, self.OnServerMenu, id = server.GetId())
        self.Bind(wx.EVT_MENU, self.OnQuitMenu, id = quit.GetId())
        
        menu.Append(settings, "&Settings")
        self.SetMenuBar(menu)
    
    def CreateControls(self):
        self.button_play = wx.Button(self.panel, -1, "Play / Pause", size = const.BUTTON_SIZE)
        self.button_stop = wx.Button(self.panel, -1, "Stop", size = const.BUTTON_SIZE)
        
        self.button_play.Bind(wx.EVT_BUTTON, self.OnPlay)
        self.button_stop.Bind(wx.EVT_BUTTON, self.OnStop)
    
    def SetLayout(self):
        vbox = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        
        hbox.Add(self.button_play, 0, wx.ALIGN_CENTER | wx.ALL, 4)
        hbox.Add(self.button_stop, 0, wx.ALIGN_CENTER | wx.ALL, 4)
        vbox.Add(hbox, 0, wx.ALIGN_CENTER)
        
        self.panel.SetSizer(vbox)
        self.Layout()
        self.Centre()
        self.Show()
    
    def ServerConnect(self):
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.connect((self.server, const.PORT))
        except socket.error, msg:
            return
        
        self.communicator = Process(target = self.Communicate)
        self.communicator.start()
    
    def Communicate(self):
        while True:
            if not self.socket:
                break
            data = self.socket.recv(1024)
            if not data:
                break
            data = data.replace('\n', '')
            if self.player in const.PLAYERS.keys() and data in const.PLAYERS[self.player]:
                pass
    
    def OnPlay(self, event):
        self.Play()
    
    def OnStop(self, event):
        self.Stop()
    
    def OnPlayerMenu(self, event):
        try:
            player = event.GetEventObject().FindItemById(event.GetId()).GetItemLabelText()
        except:
            return
        self.player = player
        self.storage.SetPlayer(player)
    
    def OnServerMenu(self, event):
        ServerDialog(self).Show()
    
    def OnQuitMenu(self, event):
        self.Quit()
    
    def OnTaskBarRight(self, event):
        event.GetEventObject().PopupMenu(TaskBarMenu(self))
    
    def OnTaskBarLeft(self, event):
        self.Play()
    
    def OnClose(self, event):
        self.ToggleShown()
        event.Veto()
        return False
    
    def Play(self):
        if self.socket:
            self.socket.send(const.PLAY_ACTION)
    
    def Stop(self):
        if self.socket:
            self.socket.send(const.STOP_ACTION)
    
    def ToggleShown(self):
        self.Show(not self.IsShown())
    
    def Quit(self):
        self.socket.close()
        self.communicator.terminate()
        self.tbicon.RemoveIcon()
        self.Destroy()


















