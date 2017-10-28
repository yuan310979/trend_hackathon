var list;

setTimeout(function() {
	document.getElementsByClassName("zA")[2].style.backgroundColor="red";
	list = document.getElementById(":iu");
	list.addEventListener("DOMSubtreeModified", change, false);
}, 5000);

function change() {
	setTimeout(function() {
		list = document.getElementById(":iu");
		console.log(list);
		list.addEventListener("DOMSubtreeModified", change, false);
		document.getElementsByClassName("zA")[2].style.backgroundColor="red";
	}, 1000);
}
