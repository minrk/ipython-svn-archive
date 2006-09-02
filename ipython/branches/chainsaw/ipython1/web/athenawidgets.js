// import Nevow.Athena

/*getParam from cryer.co.uk script8*/
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
        document.getElementById('targets').value = getParam('ids');
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
		document.getElementById('commandOut').innerHTML = outs;
	});
ControllerModule.CommandWidget.method(
    'changeCmd',
    function(self, cmd){
		if(cmd == 'local' || cmd == 'globals'){
			document.getElementById("targets").disabled = true
		}else{
			document.getElementById("targets").disabled = false
		}
		if(cmd == 'reset' || cmd == 'status' || cmd == 'kill' || cmd == 'globals'){
			document.getElementById("args").disabled = true
		}else{
			document.getElementById("args").disabled = false
		}
	});

ControllerModule.StatusWidget = Nevow.Athena.Widget.subclass('ControllerModule.StatusWidget');

ControllerModule.StatusWidget.method(
    'getIDs',
    function(self){
        var idform = document.getElementById('statusidform');
        idform.statusidfield.value = getParam('ids')
    });

ControllerModule.StatusWidget.method(
    'getStatus',
    function(self, id, pending, queue, hist, locals) {
        d = self.callRemote('status', id, pending, queue, hist, locals);
    });

ControllerModule.StatusWidget.method(
    'refreshStatus',
    function(self) {
        var idform = document.getElementById('statusidform');
        self.getStatus(idform.statusidfield.value, idform.pending.checked, 
            idform.queue.checked,idform.history.checked,idform.locals.checked);
    });

ControllerModule.StatusWidget.method(
    'updateStatus',
    function(self, expression) {
        document.getElementById('statusOut').innerHTML = expression;
    });

ControllerModule.ResultWidget = Nevow.Athena.Widget.subclass('ControllerModule.ResultWidget');

ControllerModule.ResultWidget.ids = 'all';

ControllerModule.ResultWidget.method(
    'getIDs',
    function(self) {
        self.ids = getParam('ids');
        document.getElementById('resultIdField').value = self.ids
        self.callRemote('setIDs', self.ids);
    });

ControllerModule.ResultWidget.method(
    'handleResult',
    function(self, result) {
        var output = document.getElementById('resultOut');
        output.innerHTML = output.innerHTML+result;
        output.scrollTop = output.scrollHeight;
    });

ControllerModule.IDWidget = Nevow.Athena.Widget.subclass('ControllerModule.IDWidget');

ControllerModule.IDWidget.method(
    'drawIDs',
    function(self, idstr){
        document.getElementById('idlist').innerHTML = idstr;
    });

ControllerModule.ChatWidget = Nevow.Athena.Widget.subclass('ControllerModule.ChatWidget');

ControllerModule.NotebookWidget = Nevow.Athena.Widget.subclass('ControllerModule.NotebookWidget');

ControllerModule.NotebookWidget.currentID = 0;
ControllerModule.NotebookWidget.selectedCell = '';

ControllerModule.NotebookWidget.method(
    'getIDs',
    function(self) {
        var ids = getParam('ids');
/*    document.getElementById('idfield').value = self.ids;*/
        self.selectedCell = ''
        self.currentID = 0;
        self.callRemote('setIDs', ids);
    });

ControllerModule.NotebookWidget.method(
    'handleOutput',
    function (self, cmd_id, id, out){
        var cell = document.getElementById(cmd_id);
        cell.lastChild.firstChild.firstChild.innerHTML = 'In&nbsp;['+id+']:';
        cell.lastChild.firstChild.lastChild.firstChild.disabled = false;
        cell.lastChild.lastChild.firstChild.innerHTML = 'Out['+id+']:';
        var output = cell.lastChild.lastChild.lastChild;
        output.innerHTML = out+'&nbsp';
    });

ControllerModule.NotebookWidget.method(
    'addIOCell',
    function(self){
        var id = self.currentID;
        self.currentID++;
        // Create an empty I/O cell
        var ioCell = document.createElement('div');
        ioCell.className = 'ioCell';
        ioCell.setAttribute('id', 'ioCell'+id);
    
        // Create an empty inOut column
        var inOut = document.createElement('div');
        inOut.className = 'inOut';

        // Create the input row within the inOut column
        var inRow = document.createElement('div');
        inRow.className = 'inRow';
        var inLabel = document.createElement('div');
        inLabel.className = 'inLabel';
        inLabel.innerHTML = 'In&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;:';
        inRow.appendChild(inLabel);
        var inContent = document.createElement('div');
        inContent.className = 'inContent';
        var textArea = document.createElement('textarea');
        textArea.rows = 1;
        textArea.setAttribute('onkeypress',
            "w = Nevow.Athena.Widget.get(this);w.resizeTextArea(this,event);");
        inContent.appendChild(textArea);
        inRow.appendChild(inContent);

        // Create the output row within the inOut column
        var outRow = document.createElement('div');
        outRow.className = 'outRow';
        var outLabel = document.createElement('div');
        outLabel.className = 'outLabel';
        outLabel.innerHTML = 'Out&nbsp;&nbsp;&nbsp;&nbsp;:';
        outRow.appendChild(outLabel);
        var outContent = document.createElement('div');
        outContent.className = 'outContent';
        outContent.innerHTML = '&nbsp;';
        outRow.appendChild(outContent);

        // Add the input and output rows to the inOut columns
        inOut.appendChild(inRow);
        inOut.appendChild(outRow);
    
        // Create the collapse columns
        var Collapse = document.createElement('div');
        Collapse.className = 'collapse';
        Collapse.setAttribute('onclick',
            "w = Nevow.Athena.Widget.get(this);w.toggleCollapse(this);");

        // Add the collapse and inOut columns to the I/O cell
        ioCell.appendChild(Collapse);
        ioCell.appendChild(inOut);

        // Insert the I/O cell in the correct location
        if (self.selectedCell == '')
        {
        document.getElementById('nb').appendChild(ioCell);
        }
        else
        {
        self.selectedCell.parentNode.appendChild(ioCell);
        }

        self.setCollapseHeight(ioCell);
    });

ControllerModule.NotebookWidget.method(
    'addTextCell',
    function(self){
        // Create an empty text cell
        var textCell = document.createElement('div');
        textCell.className = 'textCell';

        // Create the text column
        var textCol = document.createElement('div');
        textCol.className = 'textCol';
        var textArea = document.createElement('textarea');
        textArea.className = 'textCell';
        textArea.rows = 1;
        textArea.setAttribute('onkeypress',
            "w = Nevow.Athena.Widget.get(this);w.resizeTextArea(this,event);");
        textCol.appendChild(textArea);

        // Create the collapse columns
        var Collapse = document.createElement('div');
        Collapse.className = 'collapse';
        Collapse.setAttribute('onclick',
            "w = Nevow.Athena.Widget.get(this);w.toggleCollapse(this);");

        // Add the collapse and inOut columns to the I/O cell
        textCell.appendChild(Collapse);
        textCell.appendChild(textCol);

        // Insert the I/O cell in the correct location
        if (self.selectedCell == '')
        {
        document.getElementById('nb').appendChild(textCell);
        }
        else
        {
        self.selectedCell.parentNode.appendChild(textCell);
        }

        self.setCollapseHeight(textCell);
    });

ControllerModule.NotebookWidget.method(
    'setCollapseHeight',
    function(self, cellObj){
        //Cell.style.backgroundColor = 'blue';
        //window.alert(Cell.clientHeight - 2);
        //window.alert(Cell.className);
        //Cell.style.backgroundColor = '';

        // Iteratively fix the parents
        while (cellObj.id != 'nb')
        {
        var Collapse = cellObj.firstChild; // for some reason, the Cell sees the Collapse as the firstChild and inOut as the lastChild
        Collapse.style.height = cellObj.clientHeight - 2;

        cellObj = cellObj.parentNode;
        }
    });

ControllerModule.NotebookWidget.method(
    'resizeTextArea',
    function(self, textareaObj,e){
        // this also captures Shift+Enter to execute
        var numRows = textareaObj.value.split("\n").length; 
        textareaObj.rows = numRows;

        // textCells and I/O cells have different ways of getting the cell from the textArea
        if (textareaObj.className == 'textCell')
        {
            var Cell = textareaObj.parentNode.parentNode; // div.textCell->div.textCol->textarea.textCell
        }
        else
        {
            var Cell = textareaObj.parentNode.parentNode.parentNode.parentNode; // div.ioCell->div.inOut->div.inRow->div.Content->textarea(obj)
        }

        // textCells automatically break out of collapse when typed into
        // make I/O cells break out by showing the output
        if (Cell.className == 'ioCell')
        {
            Cell.lastChild.firstChild.firstChild.innerHTML = 'In&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;:'
            if (e.shiftKey && e.keyCode == 13)
            {
                var line = textareaObj.value;
                textareaObj.disabled = true;
                self.callRemote('execute', Cell.id, line);
            }else{
                Cell.lastChild.lastChild.style.display = '';
            }
        }

        // Make sure the height of collapse follows with the expanding or shrinking textarea
        self.setCollapseHeight(Cell);
    });

ControllerModule.NotebookWidget.method(
    'toggleCollapse',
    function(self, collapseObj)
    {
        var Cell = collapseObj.parentNode; // div.cell->div.collapse

        if (Cell.className == 'ioCell')
        {
        var inRow = Cell.lastChild.firstChild;
        var textArea = inRow.lastChild.firstChild;
        var outRow = Cell.lastChild.lastChild; // for some reason, the Cell sees the Collapse as the firstChild and inOut as the lastChild
        if (outRow.style.display == 'none')
        {
            resizeTextArea(textArea,'');
            outRow.style.display = '';
        }
        else
        {
            textArea.rows = 1;
            outRow.style.display = 'none';
        }
        }
        else if (Cell.className == 'textCell')
        {
        var textArea = Cell.childNodes[1].firstChild; // div.textCell->div.textCol->textarea.textCell
        if (textArea.rows == 1)
        {
            self.resizeTextArea(textArea,'');
        }
        else
        {
            textArea.rows = 1;
        }
        }
        self.setCollapseHeight(Cell);
    });

ControllerModule.NotebookWidget.method(
    'selectCell',
    function (self,obj)
    {
    });
