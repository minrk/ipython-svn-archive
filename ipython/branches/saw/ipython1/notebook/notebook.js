// Some class functions for data structures

function Node(obj){
    this.nodeID = obj.nodeID;
    this.dateCreated = obj.dateCreated;
    this.dateModified = obj.dateModified;
    this.comment = obj.comment;
    this.tags = obj.tags;
};

function TextCell(obj){
    node = new Node(obj);
    node.textData = obj.textData;
    node.format = obj.format;
    return node;
};

function TextCell(nodeID, dateC, dateM, comment, tags, input, output){
    node = new Node(nodeID, dateC, dateM, comment, tags);
    node.input = input;
    node.output = output;
    return node;
};

function Section(nodeID, dateC, dateM, comment, tags, title){
    node = new Node(nodeID, dateC, dateM, comment, tags);
    node.title = title;
    return node;
};

/*getParam from cryer.co.uk script8*/
getParam = function(name){
    var start=location.search.indexOf("?"+name+"=");
    if (start<0) start=location.search.indexOf("&"+name+"=");
    if (start<0) return null;
    start += name.length+2;
    var end=location.search.indexOf("&",start)-1;
    if (end<0) end=location.search.length;
    var result=location.search.substring(start,end);
    var result="";
    for(var i=start;i<=end;i++) {
        var c=location.search.charAt(i);
        result=result+(c=="+"?" ":c);
    }
    return unescape(result);
};
// globals
var currentID = 0;
var selectedCell = "";
var user = Object();
var activeNotebook = null;
/*var userID = -1;
var email = "";
var username = "";
*/
connect = function(){
    var username = getParam("username");
    if (username == null){
    	username = prompt("username?", "");
    }
    var email = getParam("email")
    if (email == null){
    	email = prompt("email?", "");
    }
    if (!selectedCell){
        selectedCell = "";
    }
    if (!currentID){
        currentID = 0;
    }
    var d = doSimpleXMLHttpRequest("/connectUser", {email:email, username:username});
    d.addCallback(setUser);
};

disconnect = function(){
    alert("disconnecting");
    return doSimpleXMLHttpRequest("/disconnectUser", {userID:user.userID}); 
};
addLoadEvent(connect);

setUser = function(req){
/*    alert(req.responseText);*/
    user = evalJSONRequest(req);
    if (!user.username){//try again
        alert("Connect User Failed");
    	var username = prompt("username?", "");
    	var email = prompt("email?", "");
        var d = doSimpleXMLHttpRequest("/connectUser", {email:email, username:username});
        d.addCallback(setUser);
        return d
    }else{
        var head = document.getElementById("header");
        head.innerHTML = "IPythonNotebook  " + user.username + ":" + user.email;
        return refreshNBTable();
    }
};

refreshNBTable = function(){
    var d = doSimpleXMLHttpRequest("/getNotebooks", {userID:user.userID});
    d.addCallback(setupNBTable);
    return d;
}

setupNBTable = function(req){
    var books = evalJSONRequest(req).notebooks;
    var data = Object();
    data.columns = ["title", "created", "modified", "permission", "notebookID"];
    data.rows = new Array;
    for (var i=0; i<books.length; i++) {
        var book = books[i];
        var row = Array();
        row.push(book.title);
        row.push(book.dateCreated);
        row.push(book.dateModified);
        if (book.userID == user.userID){
            row.push("o");
        }else{
            for (var i=0; i<books.writers.length; i++){
                if (books.writers[i] == user.userID){
                    row.push("w");
                }
            }
            if (row.length < 4){
                for (var i=0; i<books.readers.length; i++){
                    if (books.readers[i] == user.userID){
                        row.push("r");
                    }
                }
            }
            if (row.length < 4){
                alert(book.userID);
            }
        }
        row.push(book.notebookID);
        data.rows.push(row);
    }
    sortableManager.initWithData(data);
};

addNotebook = function(){
    var title = prompt("Title", "title");
    var d = doSimpleXMLHttpRequest("/addNotebook", {userID:user.userID,title:title});
    d.addCallback(refreshNBTable);
    return d;
};

getNodeTable = function(element){
    var nodeTables = getElementsByTagAndClassname("table", "section");
    nodeTables += getElementsByTagAndClassname("table", "inputCell");
    nodeTables += getElementsByTagAndClassname("table", "textCell");
    alert(nodeTables.length);
    for (var i=0;i<nodeTables.length;i++){
        var nt = nodeTables[i];
        if (isParent(nt, element)){
            return nt;
        }
    }
};

setActiveNotebook = function(nbID){
    var d = doSimpleXMLHttpRequest("/getNotebooks", {userID:user.userID, notebookID:nbID});
    d.addCallback(_setActiveNotebook);
    return d;
};

_setActiveNotebook = function(req){
    if (activeNotebook){
        var s = prompt("save before switching?").toLowerCase();
        if (s == "yes" || s == "y"){
            saveActiveNotebook();
        }
    }
    alert(req.responseText);
    activeNotebook = evalJSONRequest(req).notebooks[0];
/*    alert(activeNotebook);*/
    alert(activeNotebook.root);
    if (!activeNotebook){
        alert(req.responseText);
    }else{
        var nbtd = getElementsByTagAndClassName("td", "notebook")[0];
        nbtd.innerHTML = "";
        nbtd.appendChild(nodeTableFromJSON(activeNotebook.root));
        alert(nbtd);
    }
};

alertNode = function(node){
    var s = "id:"+node.nodeID+"\n";
    s += "nodeType:"+node.nodeType+"\n";
    alert(s);
};

nodeTableFromJSON = function(node){
/*    var klass = node.nodeType;*/
    alertNode(node);//for debug
    var t = document.createElement("table");
    t.className = node.nodeType;
    t.obj = node;
    t.setAttribute("id", node.nodeID);
    //header
    var tr = document.createElement("tr");
    var td = document.createElement("td");
    td.className = "nodeHead";
    var span = document.createElement("span");
    span.innerHTML = "nodeID:";
    td.appendChild(span);
    span = document.createElement("span");
    span.className = "nodeID";
    span.innerHTML = node.nodeID.toString();
    td.appendChild(span);
    span = document.createElement("span");
    span.innerHTML = "  |  Modified:";
    td.appendChild(span);
    span = document.createElement("span");
    span.className = "date";
    span.innerHTML = node.dateModified;
    td.appendChild(span);
    span = document.createElement("span");
    span.innerHTML = "  |  Created:";
    td.appendChild(span);
    span = document.createElement("span");
    span.className = "date";
    span.innerHTML = node.dateCreated;
    td.appendChild(span);
    tr.appendChild(td);
    t.appendChild(tr);
    
    //control
    tr = document.createElement("tr");
    td = document.createElement("td");
    td.className = "nodeActions";
    span = document.createElement("span");
    span.className = "controlLink";
    span.onClick = function(){moveNode(node.nodeID);};
    span.innerHTML = "move";
    td.appendChild(span);
    span = document.createElement("span");
    span.innerHTML = "  |  ";
    td.appendChild(span);
    span = document.createElement("span");
    span.className = "controlLink";
    span.innerHTML = "drop";
    span.onClick = function(){dropNode(node.nodeID);};
    td.appendChild(span);
    span = document.createElement("span");
    span.innerHTML = "  |  ";
    td.appendChild(span);
    span = document.createElement("span");
    span.className = "controlLink";
    span.innerHTML = "save";
    span.onClick = function(){saveNode(node.nodeID);};
    td.appendChild(span);
    tr.appendChild(td);
    t.appendChild(tr);
    
    tr = document.createElement("tr");
    td = document.createElement("td");
    for (var i=0;i<node.tags.length;i++){
        span = document.createElement("span");
        span.className = "tag";
        span.innerHTML = node.tags[i];
        td.appendChild(span);
    }
    tr.appendChild(td);
    t.appendChild(tr);

    tr = document.createElement("tr");
    td = document.createElement("td");
    td.className = "comment";
    td.innerHTML = node.comment;
    tr.appendChild(td);
    t.appendChild(tr);
    
    if (t.className == "section"){
        tr = document.createElement("tr");
        td = document.createElement("td");
        td.className = "children";
        for (var i=0; i<node.children.length; i++){
            td.appendChild(nodeTableFromJSON(node.children[i]));
        };
        tr.appendChild(td);
        t.appendChild(tr);
        
    }else if (t.className == "inputCell"){
        tr = document.createElement("tr");
        td = document.createElement("td");
        td.className = "input";
        td.innerHTML = node.input;
        tr.appendChild(td);
        t.appendChild(tr);
        
        tr = document.createElement("tr");
        td = document.createElement("td");
        td.className = "output";
        td.innerHTML = node.output;
        tr.appendChild(td);
        t.appendChild(tr);
        
    }else if (t.className == "textCell"){
        tr = document.createElement("tr");
        td = document.createElement("td");
        td.className = "format";
        td.innerHTML = node.format;
        tr.appendChild(td);
        t.appendChild(tr);
        
        tr = document.createElement("tr");
        td = document.createElement("td");
        td.className = "textData";
        td.innerHTML = node.textData;
        tr.appendChild(td);
        t.appendChild(tr);
    }
    return t;
};


handleOutput = function(cmd_id, id, out){
    var cell = document.getElementById(cmd_id);
    cell.lastChild.firstChild.firstChild.innerHTML = "In&nbsp;["+id+"]:";
    cell.lastChild.firstChild.lastChild.firstChild.disabled = false;
    cell.lastChild.lastChild.firstChild.innerHTML = "Out["+id+"]:";
    var output = cell.lastChild.lastChild.lastChild;
    output.innerHTML = out+"&nbsp";
};




addIOCell = function(){
    var id = currentID;
    currentID++;
    // Create an empty I/O cell
    var ioCell = document.createElement("div");
    ioCell.className = "ioCell";
    ioCell.setAttribute("id", "ioCell"+id);

    // Create an empty inOut column
    var inOut = document.createElement("div");
    inOut.className = "inOut";

    // Create the input row within the inOut column
    var inRow = document.createElement("div");
    inRow.className = "inRow";
    var inLabel = document.createElement("div");
    inLabel.className = "inLabel";
    inLabel.innerHTML = "In&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;:";
    inRow.appendChild(inLabel);
    var inContent = document.createElement("div");
    inContent.className = "inContent";
    var textArea = document.createElement("textarea");
    textArea.rows = 1;
    textArea.setAttribute("onkeypress","resizeTextArea(this,event);");
    inContent.appendChild(textArea);
    inRow.appendChild(inContent);

    // Create the output row within the inOut column
    var outRow = document.createElement("div");
    outRow.className = "outRow";
    var outLabel = document.createElement("div");
    outLabel.className = "outLabel";
    outLabel.innerHTML = "Out&nbsp;&nbsp;&nbsp;&nbsp;:";
    outRow.appendChild(outLabel);
    var outContent = document.createElement("div");
    outContent.className = "outContent";
    outContent.innerHTML = "&nbsp;";
    outRow.appendChild(outContent);

    // Add the input and output rows to the inOut columns
    inOut.appendChild(inRow);
    inOut.appendChild(outRow);

    // Create the collapse columns
    var Collapse = document.createElement("div");
    Collapse.className = "collapse";
    Collapse.setAttribute("onclick","toggleCollapse(this);");

    // Add the collapse and inOut columns to the I/O cell
    ioCell.appendChild(Collapse);
    ioCell.appendChild(inOut);

    // Insert the I/O cell in the correct location
    if (selectedCell == ""){
        document.getElementById("nb").appendChild(ioCell);
    }
    else{
        selectedCell.parentNode.appendChild(ioCell);
    }
    setCollapseHeight(ioCell);
};


addTextCell = function(){
        // Create an empty text cell
        var textCell = document.createElement("div");
        textCell.className = "textCell";

        // Create the text column
        var textCol = document.createElement("div");
        textCol.className = "textCol";
        var textArea = document.createElement("textarea");
        textArea.className = "textCell";
        textArea.rows = 1;
        textArea.setAttribute("onkeypress","resizeTextArea(this,event);");
        textCol.appendChild(textArea);

        // Create the collapse columns
        var Collapse = document.createElement("div");
        Collapse.className = "collapse";
        Collapse.setAttribute("onclick","toggleCollapse(this);");

        // Add the collapse and inOut columns to the I/O cell
        textCell.appendChild(Collapse);
        textCell.appendChild(textCol);

        // Insert the I/O cell in the correct location
        if (selectedCell == ""){
            document.getElementById("nb").appendChild(textCell);
        }
        else{
            selectedCell.parentNode.appendChild(textCell);
        }

        setCollapseHeight(textCell);
};

setCollapseHeight = function(cellObj){
        //Cell.style.backgroundColor = "blue";
        //window.alert(Cell.clientHeight - 2);
        //window.alert(Cell.className);
        //Cell.style.backgroundColor = "";

        // Iteratively fix the parents
        while (cellObj.id != "nb"){
        var Collapse = cellObj.firstChild; // for some reason, the Cell sees the Collapse as the firstChild and inOut as the lastChild
        Collapse.style.height = cellObj.clientHeight - 2;

        cellObj = cellObj.parentNode;
        }
};

resizeTextArea = function(textareaObj,e){
        // this also captures Shift+Enter to execute
        var numRows = textareaObj.value.split("\n").length; 
        textareaObj.rows = numRows;

        // textCells and I/O cells have different ways of getting the cell from the textArea
        if (textareaObj.className == "textCell"){
            var Cell = textareaObj.parentNode.parentNode; // div.textCell->div.textCol->textarea.textCell
        }
        else{
            var Cell = textareaObj.parentNode.parentNode.parentNode.parentNode; // div.ioCell->div.inOut->div.inRow->div.Content->textarea(obj)
        }

        // textCells automatically break out of collapse when typed into
        // make I/O cells break out by showing the output
        if (Cell.className == "ioCell"){
            Cell.lastChild.firstChild.firstChild.innerHTML = "In&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;:"
            if (e.shiftKey && e.keyCode == 13){
                var line = textareaObj.value;
                textareaObj.disabled = true;
                self.callRemote("execute", Cell.id, line);
            }else{
                Cell.lastChild.lastChild.style.display = "";
            }
        }

        // Make sure the height of collapse follows with the expanding or shrinking textarea
        setCollapseHeight(Cell);
};

toggleCollapse = function(collapseObj){
        var Cell = collapseObj.parentNode; // div.cell->div.collapse

        if (Cell.className == "ioCell"){
            var inRow = Cell.lastChild.firstChild;
            var textArea = inRow.lastChild.firstChild;
            var outRow = Cell.lastChild.lastChild; // for some reason, the Cell sees the Collapse as the firstChild and inOut as the lastChild
            if (outRow.style.display == "none"){
                resizeTextArea(textArea,"");
                outRow.style.display = "";
            }
            else{
                textArea.rows = 1;
                outRow.style.display = "none";
            }
        }else if (Cell.className == "textCell"){
            var textArea = Cell.childNodes[1].firstChild; // div.textCell->div.textCol->textarea.textCell
            if (textArea.rows == 1){
                resizeTextArea(textArea,"");
            }
            else{
                textArea.rows = 1;
            }
        }
        setCollapseHeight(Cell);
};

selectCell = function(obj){
};

