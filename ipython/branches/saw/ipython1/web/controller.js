function focusInput() {
    var il = document.inputForm.inputLine;
    il.focus();
    il.value = '';
    scrollDown();
}

function scrollDown() {
	var content = document.getElementById('content');
    content.scrollTop = content.scrollHeight;
}

function removeNode(nodeId) {
    var node = window.document.getElementById(nodeId);
    node.parentNode.removeChild(node);
}

function changeId(old, newe) {
    window.document.getElementById(old).id = newe;
}

function onResize(){
    var h = document.getElementById('headerDiv');
	var Y = window.innerHeight - 2*h.clientHeight;
	if(400 > Y){
	    Y = 400;
	}
	document.getElementById('content').style.height = ""+Y+"px";
}
