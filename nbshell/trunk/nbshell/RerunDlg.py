import sys
import  wx

from nbshell.utils import *

#Some predefined filters
FILTER_NONE = lambda x:True
FILTER_NUMERIC = lambda x:x.isdigit()

class MyValidator(wx.PyValidator):
    """A validator which can transfer and validate data"""
    def __init__(self, validate = lambda val:None,
                 getvalue = lambda wnd:None,  
                 setvalue = lambda wnd, val:True,
                 fromfunc = lambda value:True,
                 tofunc = lambda:None):
        """Initialize the validator. Parameters:
        
        'validate' - callable. It has one parameter, the value of the control,
        which is retrieved by 'getvalue'. If the value is valid, return None,
        if not must return an error message.

        'getvalue' - callable. When called it is given the control window as
        a parameter. Must return the value of the control
        
        'setvalue' - callable. Must set the given value to the control window.
        It has two parameters: the window and the value 
        
        'fromfunc' - called to retrieve the value. It has one parameter, the
        value to be retrieved. If the value was retrieved successfully must

        'tofunc' - called when the control must initialize itself. Has no
        parameters. Must return the value that will be set to the control. The
        returned value is set using 'setvalue'
        
        return True """
        
        wx.PyValidator.__init__(self)
        self.validate = validate
        self.getvalue = getvalue
        self.setvalue = setvalue
        self.tofunc = tofunc
        self.fromfunc = fromfunc
        
    def Validate(self, window):
        val = self.getvalue(self.GetWindow())
        error = self.validate(val)
        if error is not None:
            wx.MessageBox(error,'Error')
            return False
        else:
            return True
        
    def TransferToWindow(self):
        self.setvalue(self.GetWindow(), self.tofunc())
        return True

    def TransferFromWindow(self):
        return self.fromfunc(self.getvalue(self.GetWindow()))
    
    def Clone(self):
        return MyValidator(self.validate, self.getvalue, self.setvalue, self.fromfunc, self.tofunc)

class TextValidator(MyValidator):
    """Text validator. Can be used to validate controls allowing text input.
    If your control accepts EVT_CHAR events then you can use this validator"""
    def __init__(self, filter = FILTER_NONE, validate = lambda val:None,
                 getvalue = wx.TextCtrl.GetValue,
                 setvalue = wx.TextCtrl.SetValue,
                 fromfunc = lambda val:True,
                 tofunc = lambda:''):
        """Initialize the validator. 'filter' is a function which is called on
        each EVT_CHAR event with the character as a parameter. If the result
        is True the character will be accepted. See MyValidator for
        description of the other parameters. The default values for
        'getvalue', and 'setvalue' are for wx.TextCtrl controls."""
        
        MyValidator.__init__(self, validate, getvalue, setvalue, fromfunc, tofunc)
        self.filter = filter
        self.Bind(wx.EVT_CHAR, self.OnChar)
        
    def Clone(self):
        return TextValidator(self.filter, self.validate, self.getvalue,
                           self.setvalue, self.fromfunc, self.tofunc)

    def OnChar(self, evt):
        key = evt.KeyCode()
        if key < wx.WXK_SPACE or key==wx.WXK_DELETE or key>255:
            evt.Skip()
            return
        if self.filter(chr(key)):
            evt.Skip()
            return
        elif not wx.Validator_IsSilent():
            wx.Bell()
        return
    

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
        
        #Set the values that will store the result of the dialog
        self.logid = self.choices[0]
        self.choice = 0 #0-all, 1- from-to, 2-list
        self.slice = slice(0, sys.maxint) # the result if self.choice is 1
        self.list = [] #A list of numbers, used if self.choice is 2
        
        #Create the dialog
        pre = wx.PreDialog()
        pre.Create(parent, ID, title, pos, size, style)
        self.PostCreate(pre)

        sizer = wx.BoxSizer(wx.VERTICAL)

        box = wx.BoxSizer(wx.HORIZONTAL)
        label = wx.StaticText(self, -1, "Choose log:")
        box.Add(label, 0, wx.ALIGN_CENTRE|wx.ALL, 5)
        def from_logch(val):
            print '--------->',val
            self.logid = val
        self.logch = wx.Choice(self, -1, choices = self.choices, validator =\
                               MyValidator(getvalue = wx.Choice.GetStringSelection,\
                                           fromfunc = from_logch))
        self.logch.Select(0)
        box.Add(self.logch, 1, wx.ALIGN_CENTRE|wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5)
        
        box = wx.BoxSizer(wx.HORIZONTAL)

        def RbValidator(num):
            """A validator for the radio buttons"""
            def from_rb(val):
                if val is not None:
                    self.choice = val

            return MyValidator(getvalue = lambda wnd: ifelse(wx.RadioButton.GetValue(wnd),num, None),
                               fromfunc = from_rb)
        
        self.rbAll = wx.RadioButton(self, -1, "All", style = wx.RB_GROUP, validator=RbValidator(0))
        box.Add(self.rbAll, 1, wx.ALL|wx.ALIGN_CENTER,5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL,0)
        
        box = wx.BoxSizer(wx.HORIZONTAL)
        def from_FromTo(b):
            def f(val):
                if b:
                    self.slice = slice(default(lambda:int(val),0), self.slice.stop)
                else:
                    self.slice = slice(self.slice.start, default(lambda:int(val), sys.maxint))
            return f
        
        self.rbFrom = wx.RadioButton(self, -1, "From:", validator=RbValidator(1))
        box.Add(self.rbFrom,0,wx.ALL,5)
        self.txFrom = wx.TextCtrl(self, -1, '0', validator =\
                                  TextValidator(FILTER_NUMERIC, fromfunc = from_FromTo(True)))
        self.txFrom.Disable()
        box.Add(self.txFrom,1,wx.ALL,5)
        self.lbTo = wx.StaticText(self, -1, 'To:')
        self.lbTo.Disable()
        box.Add(self.lbTo,0,wx.ALL,5)
        self.txTo = wx.TextCtrl(self, -1, 'TODO', validator =\
                                TextValidator(FILTER_NUMERIC, fromfunc=from_FromTo(False)))
        self.txTo.Disable()
        box.Add(self.txTo, 1,wx.ALL,5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL,0)
        
        box = wx.BoxSizer(wx.HORIZONTAL)

        def from_List(val):
            self.list = [int(x) for x in val.split(',') if x != '']
        
        self.rbList = wx.RadioButton(self, -1, "List:", validator = RbValidator(2))
        box.Add(self.rbList, 0, wx.ALL,5)
        self.txList = wx.TextCtrl(self, -1, '', validator =\
            TextValidator(filter = lambda v:v==',' or FILTER_NUMERIC(v),\
                          fromfunc = from_List))

        self.txList.Disable()
        box.Add(self.txList, 1, wx.ALL, 5)
        sizer.Add(box, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL,0)

        line = wx.StaticLine(self, -1, size=(20,-1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW|wx.ALIGN_CENTER_VERTICAL|wx.RIGHT|wx.TOP, 5)

        btnsizer = wx.StdDialogButtonSizer()
        btn = wx.Button(self, wx.ID_OK)
        btn.SetDefault()
        btnsizer.AddButton(btn)
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
