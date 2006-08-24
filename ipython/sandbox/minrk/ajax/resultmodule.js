// import Nevow.Athena

ResultModule = {};

ResultModule.ResultWidget = Nevow.Athena.Widget.subclass('ResultModule.ResultWidget');

ResultModule.ResultWidget.method(
    'echo',
    function(self, argument) {
        alert("Echoing " + argument);
        return argument;
    });

ResultModule.ResultWidget.method(
    'clicked',
    function(self) {
        self.callRemote('echo', 'hello, world');
    });

ResultModule.ResultWidget.method(
    'handleResult',
    function(self, result) {
        var output = getElement('output');
        output.innerHTML = output.innerHTML+result;
        output.scrollTop = output.scrollHeight;
    });
