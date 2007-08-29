/********    mouseover menus    ********/




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
var gapID = 0;
var selectedCell = "";
var user = Object();
var activeNotebook = null;
var pending = [];

/*********************** load/unload functions ********************/
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
    if (!gapID){
        gapID = 0;
    }
    if (!activeNotebook){
        activeNotebook = null;
    }
    if (!pending){
        pending = [];
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

/*********************** sidebar functions ********************/
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
/*    alert(nodeTables.length);*/
    for (var i=0;i<nodeTables.length;i++){
        var nt = nodeTables[i];
        if (isParent(nt, element)){
            return nt;
        }
    }
};

setActiveNotebook = function(nbID){
    if (activeNotebook){
        var s = prompt("save before switching?").toLowerCase();
        if (s == "yes" || s == "y"){
            saveActiveNotebook();
        }
    }
    var d = doSimpleXMLHttpRequest("/getNotebooks", {userID:user.userID, notebookID:nbID});
    d.addCallback(_setActiveNotebook);
    return d;
};

_setActiveNotebook = function(req){
    activeNotebook = evalJSONRequest(req).notebooks[0];
    if (!activeNotebook){
        alert(req.responseText);
    }else{
        var nbtd = getElementsByTagAndClassName("td", "notebook")[0];
        nbtd.innerHTML = "";
        nbtd.appendChild(nodeTableFromJSON(activeNotebook.root));
    }
};

refreshNotebook = function(){
    if (!activeNotebook){
        alert("No Active Notebook!");
        return;
    }
    var d = doSimpleXMLHttpRequest("/getNotebooks", {userID:user.userID, notebookID:activeNotebook.notebookID});
    d.addCallback(_setActiveNotebook);
    return d;
};

/**** utility functions ******/

alertNode = function(node){
    var s = "id:"+node.nodeID+"\n";
    s += "nodeType:"+node.nodeType+"\n";
    alert(s);
};

getMyTable = function(element){
    while ((element.tagName != "TABLE") && element.tagName != "BODY"){
        element = element.parentNode;
    }
    return element;
};

getMySection = function(element){
    element = element.parentNode; // ensure that I don't get me back
    while ((element.tagName != "TABLE" || element.className != "section") && element.tagName != "BODY"){
        element = element.parentNode;
    }
    return element;
};

getMyChildren = function(section){
    return section.childNodes[section.childNodes.length-1].cells[0];
};

previousNode = function(node){
    var childrenTD = getMyChildren(getMySection(node));
    alert("TBimp")
};

isPending = function(nodeID){
    for (var i=0; i<pending.length; i++){
        if (nodeID == pending[i]){
            return true;
        }
    }
    return false;
}

/*********************** main notebook functions ********************/

gapTable = function(index){
    var t = document.createElement("table");
    t.className = "gap";
    t.id = index;
    //control
    var tr = document.createElement("tr");
    var td = document.createElement("td");
    td.className = "gap";
    td.innerHTML = "Insert:&nbsp;";
    span = document.createElement("span");
    span.className = "controlLink";
    span.onclick = function(){addSection(t);};
/*    span.sett*/
    span.innerHTML = "Section";
    td.appendChild(span);
    span = document.createElement("span");
    span.innerHTML = "&nbsp;&nbsp;|&nbsp;&nbsp;";
    td.appendChild(span);
    span = document.createElement("span");
    span.className = "controlLink";
    span.innerHTML = "IOCell";
    span.onclick = function(){addCell(t, "InputCell");};
    td.appendChild(span);
    span = document.createElement("span");
    span.innerHTML = "&nbsp;&nbsp;|&nbsp;&nbsp;";
    td.appendChild(span);
    span = document.createElement("span");
    span.className = "controlLink";
    span.innerHTML = "TextCell";
    span.onclick = function(){addCell(t, "TextCell");};
    td.appendChild(span);
    tr.appendChild(td);
    t.appendChild(tr);
    
    return t;
};

nodeTableFromJSON = function(node){
    var t = document.createElement("table");
    t.className = node.nodeType;
    t.node = node;
    t.setAttribute("id", node.nodeID);
    
    //header
    var tr = document.createElement("tr");
    tr.className = "nodeHead";
    var td = document.createElement("td");
    if (node.nodeType == "section"){
        td.className = "sectionTitle";
        td.setAttribute("onclick","updateTitle(this);");
        td.innerHTML = node.title;
    }else{
        td.className = "cellTitle";
        td.innerHTML = node.nodeType;
    }
    tr.appendChild(td);
    td = document.createElement("td");
    td.className = "nodeHead";
    td.innerHTML = " Modified:";
    var span = document.createElement("span");
    span.className = "date";
    span.innerHTML = node.dateModified;
    td.appendChild(span);
    td.innerHTML += " Created:";
    span = document.createElement("span");
    span.className = "date";
    span.innerHTML = node.dateCreated;
    td.appendChild(span);
    td.innerHTML += " nodeID:";
    span = document.createElement("span");
    span.className = "nodeID";
    span.innerHTML = node.nodeID.toString();
    td.appendChild(span);
    tr.appendChild(td);
    td = document.createElement("td");
    td.rowSpan = 6;
    td.className = "collapse";
    td.setAttribute("onclick", "toggleCollapse(this);");
    tr.appendChild(td);
    t.appendChild(tr);
    //control
    tr = document.createElement("tr");
    td = document.createElement("td");
    td.setAttribute("colspan", 2);
    td.className = "nodeActions";
    span = document.createElement("span");
    span.className = "controlLink";
    span.onclick = function(){moveNode(node.nodeID);};
    span.innerHTML = "move";
    td.appendChild(span);
    span = document.createElement("span");
    span.innerHTML = "&nbsp;&nbsp;|&nbsp;&nbsp;";
    td.appendChild(span);
    span = document.createElement("span");
    span.className = "controlLink";
    span.innerHTML = "drop";
    span.onclick = function(){dropNode(node.nodeID);};
    td.appendChild(span);
    span = document.createElement("span");
    span.innerHTML = "&nbsp;&nbsp;|&nbsp;&nbsp;";
    td.appendChild(span);
    span = document.createElement("span");
    span.className = "controlLink";
    span.innerHTML = "save";
    span.onclick = function(){saveNode(node.nodeID);};
    td.appendChild(span);
    tr.appendChild(td);
    t.appendChild(tr);
    
    tr = document.createElement("tr");
    td = document.createElement("td");
    td.setAttribute("colspan", 2);
    for (var i=0;i<node.tags.length;i++){
        span = document.createElement("span");
        span.className = "tag";
        span.setAttribute("onclick", "removeTag(this);");
        span.innerHTML = node.tags[i];
        td.appendChild(span);
        td.innerHTML += ", ";
    }
    ta = document.createElement("textarea");
    ta.className = "tag";
    ta.value = "add tag";
    ta.onfocus = function(){this.value = "";};
    ta.setAttribute("onblur", "updateTags(this, event);");
    ta.setAttribute("onkeypress", "maybeUpdateTags(this, event);");
/*    ta.setAttribute("onkeypress", "resizeTagArea(this, event);");*/
    td.appendChild(ta);
    tr.appendChild(td);
    t.appendChild(tr);

    tr = document.createElement("tr");
    td = document.createElement("td");
/*    td.colspan = 2;*/
    td.setAttribute("colspan", 2);
    td.className = "comment";
    var ta = document.createElement("textarea");
    ta.className = "comment";
    ta.setAttribute("onblur","updateTextArea(this,event);");
    ta.setAttribute("onkeypress", "resizeTextArea(this, event);");
    td.appendChild(ta);
    if (node.comment.length < 1){
        ta.value = "comments";
        ta.onfocus = function(){
            this.value = "";
            this.onfocus = null;
            };
    }else{
        ta.value = node.comment;
    }
    tr.appendChild(td);
    t.appendChild(tr);
    resizeTextArea(ta,null);
/*    alertNode(node);*/
    
    if (t.className == "section"){
        tr = document.createElement("tr");
        td = document.createElement("td");
        td.setAttribute("colspan", 2);
        td.className = "children";
        td.appendChild(gapTable(0));
        for (var i=0; i<node.children.length; i++){
            td.appendChild(nodeTableFromJSON(node.children[i]));
            td.appendChild(gapTable(node.notebookID, i+1));
        };
        tr.appendChild(td);
        t.appendChild(tr);
/*        alert(td.abbr);*/
        
    }else if (t.className == "inputCell"){
        tr = document.createElement("tr");
        td = document.createElement("td");
        td.setAttribute("colspan", 2);
        var div = document.createElement("div");
        div.className = "inLabel";
        div.innerHTML = "In&nbsp;&nbsp;&nbsp;&nbsp;[&nbsp;&nbsp;]:";
        td.appendChild(div);
        div = document.createElement("div");
        div.className = "inContent";
        ta = document.createElement("textarea");
        ta.setAttribute("onblur","updateTextArea(this,event);");
        ta.setAttribute("onkeypress", "resizeTextArea(this, event);");
        ta.className = "input";
        ta.value = node.input;
        if (isPending(node.nodeID)){
            ta.disabled = true;
        }
        div.appendChild(ta);
        td.appendChild(div);
        tr.appendChild(td);
        t.appendChild(tr);
        resizeTextArea(ta,null);
        
        tr = document.createElement("tr");
        td = document.createElement("td");
        td.setAttribute("colspan", 2);
        div = document.createElement("div");
        div.className = "outLabel";
        div.innerHTML = "Out&nbsp;[&nbsp;&nbsp;]:";
        td.appendChild(div);
        div = document.createElement("div");
        div.className = "outContent";
        if (node.output.length < 1 || isPending(node.nodeID)){
            div.innerHTML = "&nbsp;";
        }else{
            div.innerHTML = node.output.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/\n/g,"<br>\n");
        }
        td.appendChild(div);
        tr.appendChild(td);
        t.appendChild(tr);
        
    }else if (t.className == "textCell"){
        tr = document.createElement("tr");
        td = document.createElement("td");
        td.setAttribute("colspan", 2);
        ta = document.createElement("textarea");
        ta.className = "format";
        ta.setAttribute("onblur","updateTextArea(this,event);");
        ta.setAttribute("onkeypress", "resizeTextArea(this, event);");
        if (!node.format || node.format.length < 1){
            ta.value = "format";
            ta.onfocus = function(){
                this.value = "";
                this.onfocus = null;
                };
        }else{
            ta.value = node.format;
        }
        td.appendChild(ta);
        tr.appendChild(td);
        t.appendChild(tr);
        resizeTextArea(ta,null);
        
        tr = document.createElement("tr");
        td = document.createElement("td");
        td.setAttribute("colspan", 2);
        ta = document.createElement("textarea");
        ta.className = "textData";
        ta.setAttribute("onblur","updateTextArea(this,event);");
        ta.setAttribute("onkeypress", "resizeTextArea(this, event);");
        if (node.textData.length < 1){
            ta.value = "Text Data";
            ta.onfocus = function(){
                this.value = "";
                this.onfocus = null;
                };
        }else{
            ta.value = node.textData;
        }
        td.appendChild(ta);
        tr.appendChild(td);
        t.appendChild(tr);
        resizeTextArea(ta,null);
    }
/*    alertNode(node);//for debug*/
    
    return t;
};
updateTitle = function(titleTD){
    var t = getMyTable(titleTD);
    newtitle = prompt("New Title", t.node.title)
    if (t.node.title == newtitle){
        return;
    }
    args = {};
    args.userID = user.userID;
    args.nodeID = t.node.nodeID;
    args["title"]= newtitle;
    var d = doSimpleXMLHttpRequest("/editNode", args);
    d.addCallback(_updateNode, t);
};
updateTextArea = function(textarea){
    var t = getMyTable(textarea);
/*    var nodeID = t.node.nodeID;*/
    if (t.node[textarea.className] == textarea.value){
        //no change
        return;
    }
    args = {};
    args.userID = user.userID;
    args.nodeID = t.node.nodeID;
    args[textarea.className]= textarea.value;
/*    alert(textarea.className);*/
    var d = doSimpleXMLHttpRequest("/editNode", args);
    d.addCallback(_updateNode, t);
    return d;
};
_updateNode = function(t,req){
    var node = evalJSONRequest(req);
    var newt = nodeTableFromJSON(node);
    swapDOM(t, newt);
};
/********** tag functions    ***********/
stripTag = function(tag){
    while (tag.length > 0 && tag[0] == " "){
        tag = tag.substring(1);
    }
    while (tag.length > 0 && tag[tag.length-1] == " "){
        tag = tag.substring(0,tag.length-2);
    }
    return tag;
};
getTags = function(table){
    var spanlist = getElementsByTagAndClassName("SPAN", "tag");
    var taglist = new Array;
    for (i=0; i < spanlist.length; i++){
        if (isParent(spanlist[i], table)){
            taglist.push(spanlist[i].innerHTML);
/*            alert(spanlist[i].innerHTML);*/
        }
    }
    return taglist;
};
isin = function(element, array){
    for (var i=0;i<array.length;i++){
        if (element == array[i]){
            return true;
        }
    }
    return false;
};
maybeUpdateTags = function(textarea, event){
    if (event.keyCode == 13){
        updateTags(textarea);
    }
};
updateTags = function(textarea){
    var t = getMyTable(textarea);
/*    var nodeID = t.node.nodeID;*/
    var args = {};
    args.userID = user.userID;
    args.nodeID = t.node.nodeID;
    var l = textarea.value.split(",");
    textarea.value = "";
    if (l.length == 0){
        return;
    }
    args.tags = getTags(t);
    var len = args.tags.length;
    for (var i=0; i < l.length; i++){
        var tag = stripTag(l[i]);
        if (tag != "" && !isin(tag, args.tags)){
            args.tags.push(tag);
        }
    }
    if (args.tags.length <= len){
        return;
    }
/*    alert(nodeID);*/
    var d = doSimpleXMLHttpRequest("/editNode", args);
    d.addCallback(_updateNode, t);
};
removeTag = function(span){
    alert(span);
    var t = getMyTable(span);
    var args = {};
    args.userID = user.userID;
    args.nodeID = t.node.nodeID;
    span.parentNode.removeChild(span);
    args.tags = getTags(t);
    var d = doSimpleXMLHttpRequest("/editNode", args);
    d.addCallback(_updateNode, t);
}
addSection = function(gapt){
    var args = {};
    args.userID = user.userID;
    var t = getMyTable(gapt);
    var parentT = getMySection(t);
    var childrenTD = getMyChildren(parentT);
    args.parentID = parentT.node.nodeID;
    for (var i=0;i<childrenTD.childNodes.length;i++){
        if (childrenTD.childNodes[i] == t){
            args.index = i/2;
            break;
        }
    }
    args.title = prompt("Title");
    args.nodeType = "Section";
    var d = doSimpleXMLHttpRequest("/addNode",args);
    d.addCallback(refreshNotebook);
};
addCell = function(gapt, nodeType){
    var args = {};
    args.userID = user.userID;
    var t = getMyTable(gapt);
    var parentT = getMySection(t);
    var childrenTD = getMyChildren(parentT);
    args.parentID = parentT.node.nodeID;
    for (var i=0;i<childrenTD.childNodes.length;i++){
        if (childrenTD.childNodes[i] == t){
            args.index = i/2;
            break;
        }
    }
    args.nodeType = nodeType;
    var d = doSimpleXMLHttpRequest("/addNode",args);
    d.addCallback(refreshNotebook);
};

dropNode = function(nodeID){
    var args = {};
    args.userID = user.userID;
    args.nodeID = nodeID;
    var d = doSimpleXMLHttpRequest("/dropNode",args);
    d.addCallback(refreshNotebook);
};

moveNode = function(nodeID){
    var args = {};
    args.userID = user.userID;
    args.nodeID = nodeID;
    args.parentID = prompt("new parent?");
    args.index = prompt("new Location?");
    var d = doSimpleXMLHttpRequest("/moveNode",args);
    d.addCallback(refreshNotebook);
};

execute = function(nodeID){
    var args = {};
    args.userID = user.userID;
    args.nodeID = nodeID;
    var d = doSimpleXMLHttpRequest("/execute",args);
    d.addCallback(_execute, nodeID);
    d.addCallback(refreshNotebook);
    return d;
};
_execute = function(nodeID, result){
    for(var i=0; i<pending.length;i++){
        if(nodeID == pending[i]){
            pending = pending.slice(0,i).concat(pending.slice(i+1));
        }
    }
    return result;
};

dumpNotebook = function(){
    if (!activeNotebook){
        alert("No Active Notebook");
    }else{
/*        alert(document.location);*/
        var loc = document.location;
        if (loc.search.indexOf("?") > -1){
            loc = loc.href.substring(0,loc.search.indexOf("?"));
        }
        var qs = queryString({userID:user.userID, notebookID:activeNotebook.notebookID});
        window.open(loc+"notebook.xml?"+qs);
    }
};

dropNotebook = function(){
    if (!activeNotebook){
        alert("No Active Notebook");
    }else{
        var d = doSimpleXMLHttpRequest("/dropNotebook",{userID:user.userID, notebookID:activeNotebook.notebookID});
        d.addCallback(refreshNBTable)
        activeNotebook = null;
        var nbtd = getElementsByTagAndClassName("td", "notebook")[0];
        nbtd.innerHTML = "";
    }
}


handleOutput = function(cmd_id, id, out){
    var cell = document.getElementById(cmd_id);
    cell.lastChild.firstChild.firstChild.innerHTML = "In&nbsp;["+id+"]:";
    cell.lastChild.firstChild.lastChild.firstChild.disabled = false;
    cell.lastChild.lastChild.firstChild.innerHTML = "Out["+id+"]:";
    var output = cell.lastChild.lastChild.lastChild;
    output.innerHTML = out+"&nbsp";
};


resizeTextArea = function(textarea,e){
        // this also captures Shift+Enter to execute
        var numRows = textarea.value.split("\n").length;
        var td = textarea.parentNode; // td
        if (e && e.keyCode == 13 && !(e.shifKey && td.className == "inContent")){
            textarea.style.height = (numRows+1 || 1).toString()+".2em";
        }else{
            textarea.style.height = (numRows || 1).toString()+".2em";
        }
        if (td.className == "inContent"){
/*            Cell.lastChild.firstChild.firstChild.innerHTML = "In&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;:"*/
            if (e && e.shiftKey && e.keyCode == 13){//shift-enter
                var d = updateTextArea(textarea, true);
                var t = getMyTable(textarea);
                pending.push(t.node.nodeID);
                textarea.disabled = true;
                if (!d){
                    execute(t.node.nodeID).addCallback(refreshNotebook);
                }else{
                    d.addCallback(function(){
                        execute(t.node.nodeID).addCallback(refreshNotebook);
                    });
                }
            }else{
                //proper action tbd
            }
        }
};

toggleCollapse = function(collapseObj){
    var t = getMyTable(collapseObj);
    for (var i=1; i<t.childNodes.length; i++){
        var row = t.childNodes[i];
        if (row.style.display == "none"){
            row.style.display = "";
        }else{
            row.style.display = "none";
        }
    }
};
