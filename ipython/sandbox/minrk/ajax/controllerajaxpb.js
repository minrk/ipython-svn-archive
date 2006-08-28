// import Nevow.Athena
/*from cryer.co.uk script8*/
function getParam(name)
{
  var start=location.search.indexOf("?"+name+"=");
  if (start<0) start=location.search.indexOf("&"+name+"=");
  if (start<0) return 'all';
  start += name.length+2;
  var end=location.search.indexOf("&",start)-1;
  if (end<0) end=location.search.length;
  var result=location.search.substring(start,end);
  var result='';
  for(var i=start;i<=end;i++) {
    var c=location.search.charAt(i);
    result=result+(c=='+'?' ':c);
  }
  return unescape(result);
}

ControllerModule = {};

ControllerModule.CommandWidget = Nevow.Athena.Widget.subclass('ControllerModule.CommandWidget');

ControllerModule.CommandWidget.method(
    'getIDs',
    function(self) {
        getElement('targets').value = getParam('ids');
    });
    
ControllerModule.CommandWidget.method(
    'submitCommand',
    function(self, cmd, targets, args){
		self.commandOutput(cmd+'('+targets+','+args+') pending...');
		d = self.callRemote(cmd, targets, args);
	});

ControllerModule.CommandWidget.method(
    'commandOutput',
    function(self, outs){
		getElement('commandOut').innerHTML = outs;
	});
ControllerModule.CommandWidget.method(
    'changeCmd',
    function(self, cmd){
		if(cmd == 'local' || cmd == 'globals'){
			getElement("targets").disabled = true
		}else{
			getElement("targets").disabled = false
		}
		if(cmd == 'reset' || cmd == 'status' || cmd == 'kill' || cmd == 'globals'){
			getElement("args").disabled = true
		}else{
			getElement("args").disabled = false
		}
	});

ControllerModule.StatusWidget = Nevow.Athena.Widget.subclass('ControllerModule.StatusWidget');

ControllerModule.StatusWidget.method(
    'getIDs',
    function(self){
        var idform = getElement('idform');
        idform.idfield.value = getParam('ids')
    });

ControllerModule.StatusWidget.method(
    'getStatus',
    function(self, id, pending, queue, hist, locals) {
        d = self.callRemote('status', id, pending, queue, hist, locals);
    });

ControllerModule.StatusWidget.method(
    'refreshStatus',
    function(self) {
        var idform = getElement('idform');
        self.getStatus(idform.idfield.value, idform.pending.checked, 
            idform.queue.checked,idform.history.checked,idform.locals.checked);
    });

ControllerModule.StatusWidget.method(
    'updateStatus',
    function(self, expression) {
        getElement('statusOut').innerHTML = expression;
    });

ControllerModule.ResultWidget = Nevow.Athena.Widget.subclass('ControllerModule.ResultWidget');

ControllerModule.ResultWidget.ids = 'all';

ControllerModule.ResultWidget.method(
    'getIDs',
    function(self) {
        self.ids = getParam('ids');
        self.callRemote('setIDs', self.ids);
    });

ControllerModule.ResultWidget.method(
    'handleResult',
    function(self, result) {
        var output = getElement('resultOut');
        output.innerHTML = output.innerHTML+result;
        output.scrollTop = output.scrollHeight;
    });
