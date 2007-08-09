class Node() {
    public int nodeID;
    public String dateCreated;
    public String dateModified;
    public Array  tags;
}

class TextCell(){
    public String textData;
    public String format;
}
class InputCell(){
    public String input;
    public String output;
}
class Section(){
    public String title;
}

TextCell.inherits(Node)
InputCell.inherits(Node)
Section.inherits(Node)



/*getParam from cryer.co.uk script8*/
getParam = function(name){
    var v = document.getElementById(name);
    if (v != null){
        return v.value;
    }else{
        v = document.createElement("input");
        v.setAttribute("id", name)
        v.type = "hidden";
        document.body.appendChild(v);
    }
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
    v.value = unescape(result);
    return unescape(result);
}
// globals
var currentID = 0;
var selectedCell = "";
var userID = -1;
var email = "";
var username = "";

connect = function(){
    username = getParam("username");
    if (username == null){
    	username = prompt("username?", "");
        var u = document.getElementById("username");
        u.value = username;
    }
    email = getParam("email")
    if (email == null){
    	email = prompt("email?", "");
        var e = document.getElementById("email");
        e.value = email;
    }
    if (!selectedCell){
        selectedCell = "";
    }
    if (!currentID){
        currentID = 0;
    }
    var head = document.getElementById("header");
/*    alert(document.getElementById("sidebar").width)*/
/*    alert(head);*/
/*    alert(head.value);*/
/*    alert(head.text);*/
    head.innerHTML = "IPythonNotebook  " + username + ":" + email;
/*    alert(queryString({email:email}));*/
/*    var s = queryString();*/
/*    var reqs = "/connectuser?"+s;*/
/*    alert(reqs);*/
    var d = doSimpleXMLHttpRequest("/connectuser", {email:email, username:username});
    d.addCallback(setUserID)
};

disconnect = function(){
    doSimpleXMLHttpRequest("/disconnectuser", {userID:userID});
}

setUserID = function(result){
    alert(result.responseText);
    var username = document.getElementById("username");
    username.value = username;
/*    alert(result[1]);*/
}

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

