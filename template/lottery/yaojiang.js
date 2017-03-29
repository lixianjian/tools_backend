var speed=1;
var demo2=document.getElementById("demo2");
var demo1=document.getElementById("demo1");
var demo=document.getElementById("demo");
demo2.innerHTML=demo1.innerHTML

var demo2_2=document.getElementById("demo2_2");
var demo1_2=document.getElementById("demo1_2");
var demo_2=document.getElementById("demo_2");
demo2_2.innerHTML=demo1_2.innerHTML

var demo2_3=document.getElementById("demo2_3");
var demo1_3=document.getElementById("demo1_3");
var demo_3=document.getElementById("demo_3");
demo2_3.innerHTML=demo1_3.innerHTML

function Marquee(_demo, _demo1, _demo2, move){
	if(_demo2.offsetTop-_demo.scrollTop>=65)
		_demo.scrollTop+=_demo1.offsetHeight;
	else{
		_demo.scrollTop -= move;
	}
}

var MyMar1, MyMar2, MyMar3, MyMar4, shang=0;

function flashLogo() {
	var deng = document.getElementById("shanshuo");
	if(shang == 0) {
		deng.src = "17.gif";
		shang = 1;
	} else {
		deng.src = "16.gif";
		shang = 0;
	}
}

function Marquee1(){
	Marquee(demo, demo1, demo2, 5);
}

function Marquee2(){
	Marquee(demo_2, demo1_2, demo2_2, 5);
}

function Marquee3(){
	Marquee(demo_3, demo1_3, demo2_3, 5);
}

function start() {
	document.getElementById("startButton").href="javascript:void(null);"

	start1();
	setTimeout("start2()", 1000);
	setTimeout("start3()", 2000);
	
	MyMar4=setInterval(flashLogo, 100);
	
	setTimeout("stop()", 6000);
}

function start1() {
	MyMar1=setInterval(Marquee1,speed);
}

function start2() {
	MyMar2=setInterval(Marquee2,speed);
}

function start3() {
	MyMar3=setInterval(Marquee3,speed);
}

var   images1 = "4,5,6,7,19,20,21,22,23,24";
var   images2 = "8,9,10,11,25,26,27,28,29,30";
var   images3 = "12,13,14,15,31,32,33,34,35,36";
  
var   imageArr1 = images1.split(",");
var	  imageArr2 = images2.split(",");   		
var	  imageArr3 = images3.split(",");

function   GetRnd(min,max){  
	return   parseInt(Math.random()*(max-min+1));  
}

function stop() {
	document.getElementById("startButton").href="javascript:start();";

	var orange = imageArr1[GetRnd(0, imageArr1.length-1)];
	var blue = imageArr2[GetRnd(0, imageArr2.length-1)];
	var green = imageArr3[GetRnd(0, imageArr3.length-1)];
	
	stopSet(orange, blue, green);
}

function stopSet(orange, blue, green) {
	stop1(orange);
	setTimeout("stop2(" + blue + ")", 1000);
	setTimeout("stop3(" + green + ")", 2000);
	
	clearInterval(MyMar4);
	document.getElementById("shanshuo").src = "17.gif";
}

function stop1(orange) {
	clearInterval(MyMar1);
	demo.scrollTop = 0;
	document.getElementById("orange").src = orange + ".gif";
}

function stop2(blue) {
	clearInterval(MyMar2);
	demo_2.scrollTop = 0;
	document.getElementById("blue").src = blue + ".gif";
}

function stop3(green) {
	clearInterval(MyMar3);
	demo_3.scrollTop = 0;
	document.getElementById("green").src = green + ".gif";
}