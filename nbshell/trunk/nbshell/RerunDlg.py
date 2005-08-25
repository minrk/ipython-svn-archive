import  wx

from nbshell.utils import *

class SimpleTextValidator(wx.PyValidator):
    """ Simple text validator """
    
class RerunDialog(wx.Dialog):
    def __init__(
            self, parent, ID, title, size=wx.DefaultSize, pos=wx.DefaultPosition, 
            style=wx.DEFAULT_DIALOG_STYLE
            ):

        
        self.frame = parent
        self.app = parent.app
        self.document = self.app.document
        self.sheet = self.app.document.sheet
        
        self.choices = self.document.logs.keys()
        
        #Create the dialog
        pre = wx.PreDialog()
        pre.Create(parent, ID, title, pos, size, style)
        self.PostCreate(pre)

        sizer = wx.BoxSizer(wx.VERTICAL)

        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Choose log:")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        self.logch = wx.Choice(self, -1, choices = self.choices)
        box.Add(self.logch, 1, wx.ALIGN_CENTRE|wx.ALL, 5)

        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        
        box = wx.BoxSizer(wx.HORIZONTAL)

        self.rbAll = wx.RadioButton(self, -1, "All", style = wx.RB_GROUP)
        box.Add(self.rbAll, 1, wx.ALL|wx.ALIGN_CENTER,5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL,0)
        
        box = wx.BoxSizer(wx.HORIZONTAL)
        
        self.rbFrom = wx.RadioButton(self, -1, "From:")
        box.Add(self.rbFrom,0,wx.ALL,5)
        self.txFrom = wx.TextCtrl(self, -1, '0')
        self.txFrom.Disable()
        box.Add(self.txFrom,1,wx.ALL,5)
        self.lbTo = wx.StaticText(self, -1, 'To:')
        self.lbTo.Disable()
        box.Add(self.lbTo,0,wx.ALL,5)
        self.txTo = wx.TextCtrl(self, -1, 'TODO')
        self.txTo.Disable()
        box.Add(self.txTo, 1,wx.ALL,5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL,0)
        
        box = wx.BoxSizer(wx.HORIZONTAL)

        self.rbList = wx.RadioButton(self, -1, "List:")
        box.Add(self.rbList, 0, wx.ALL,5)
        self.txList = wx.TextCtrl(self, -1, '')
        self.txList.Disable()
        box.Add(self.txList, 1, wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL,0)

        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

        btnsizer = wx.StdDialogButtonSizer()
        add
        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        btnsizer.AddButton(btn)
        wx.Ge
        btn = wx.Button(self, wx.ID_CANCEL)
        btnsizer.AddButton(btn)
        btnsizer.Realize()

        sizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)

        self.SetSizer(sizer)
        sizer.Fit(self)
        
        
        #Now set up the events
        self.rbAll.Bind(wx.EVT_RADIOBUTTON, self.OnRadioButton)
        self.rbFrom.Bind(wx.EVT_RADIOBUTTON, self.OnRadioButton)
        self.rbList.Bind(wx.EVT_RADIOBUTTON, self.OnRadioButton)
        
    def OnRadioButton(self, evt):
        id = evt.GetId()
        
        allwnds = []
        fromwnds = [self.txFrom, self.lbTo, self.txTo]
        listwnds = [self.txList]
        wnds = [(self.rbAll,allwnds),(self.rbFrom,fromwnds),(self.rbList,listwnds)]
        for wnd,lst in wnds:
            map(ifelse(wnd.GetId() == id,lambda:wx.Window.Enable,lambda:wx.Window.Disable),
                lst)
