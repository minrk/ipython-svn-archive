// import Nevow.Athena

ControllerModule = {};

ControllerModule.ControllerWidget = Nevow.Athena.Widget.subclass('ControllerModule.ControllerWidget');

ControllerModule.ControllerWidget.method(
    'commandOutput',
    function(self, result) {
/*        alert(result);*/
        var output = getElement('output');
        output.innerHTML = output.innerHTML+result+'<br/>\n';
        output.scrollTop = output.scrollHeight;
    });
    
ControllerModule.ControllerWidget.method(
    'submitCommand',
    function(self, cmd, targets, args){
/*        alert(cmd);*/
		d = self.callRemote(cmd, targets, args);
/*		d.addCallback(self.commandOutput);*/
	});
ControllerModule.ControllerWidget.method(
    'commandOutput',
    function(self, outs){
/*	    alert(outs);*/
		getElement('commandout').innerHTML = outs;
/*		return refreshStatus();*/
	});
ControllerModule.ControllerWidget.method(
    'changeCmd',
    function(self, cmd){
/*	    alert(cmd)*/
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


ControllerModule.StatusWidget = {};
ControllerModule.StatusWidget = Nevow.Athena.Widget.subclass('ControllerModule.StatusWidget');


/*ControllerModule.StatusWidget.methods(
    self.ids = 'all';
	self.command = "execute";
    function getStatus(self, id) {
        d = server.callRemote('status', id);
        d.addCallback(updateStatus);
    }
    function updateStatus(self, expression) {
        getElement('status').innerHTML = expression;
    }
	function refreshStatus(self){
		ids = getElement("idfield").value
		getStatus(ids)
	}
);
*/