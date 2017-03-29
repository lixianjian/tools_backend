//滚动速度
var speed=10;
//是否闪烁
var shang=0;
//定时器数组
var lottery_interval;
//闪烁定时器
var fla_inter_obj;
//中奖号码
var number;
//img对象数组
var img_objs = [];
//服务器返回值
var the_msg;
//公告对象
var fsa_obj = document.getElementById("fsa");
//取值索引
var index = 0;

//数组删除元素
Array.prototype.del=function(n) {　//n表示第几项，从0开始算起。
	//prototype为对象原型，注意这里为对象增加自定义方法的方法。
	if(n<0)　//如果n<0，则不进行任何操作。
		return this;
	else
		return this.slice(0,n).concat(this.slice(n+1,this.length));
	　　/*
	　　　concat方法：返回一个新数组，这个新数组是由两个或更多数组组合而成的。
	　　　　　　　　　这里就是返回this.slice(0,n)/this.slice(n+1,this.length)
	　　 　　　　　　组成的新数组，这中间，刚好少了第n项。
	　　　slice方法： 返回一个数组的一段，两个参数，分别指定开始和结束的位置。
	　　*/
}

Array.prototype.remove=function(dx)
{
　if(isNaN(dx)||dx>this.length){return false;}
　for(var i=0,n=0;i<this.length;i++)
　{
　　　if(this[i]!=this[dx])
　　　{
　　　　　this[n++]=this[i]
　　　}
　}
　this.length-=1
}

function test_remove(){
	var arr1 = new Array(2,3,4,4);
	arr1.remove(0);
	alert(arr1.length);
	alert(arr1);
}

//初始化img数组
function set_img_objs(){
	for (var i = 1; i < 11 + 1; i++){
		//var _id = "img_"+i;
		//alert(_id);
		//var obj1 = document.getElementById(_id);
		//alert(obj1);
		img_objs.push(document.getElementById("img_"+i));
	}
}

//获取随机值
function GetRnd(min,max){
	var offset = arguments[2] ? arguments[2] : 0;
	return parseInt(Math.random()*(max-min+1)+offset);
}

//给img赋值
function set_img(){
	//alert(number);
	for (var i = 0; i < number.length; i++){
		//img_objs[i].src = GetRnd(4, 37, 4) + ".gif";
		//img_objs[i].src = "/media/images/lottery/"+number[i] + ".gif";
		//alert(i);
		img_objs[i].innerHTML = number[i];
	}
}

//获取获奖号码
function set_number(arr){
	//alert(index+" "+num_len);
	//number = numbers[index % num_len];
	//index++;
	//index = index % num_len;
	//alert(index);
	index = GetRnd(0,arr.length-1);
	number = arr[index];
	//alert(number);
}

//摇号
function Marquee() {
	set_number(numbers);
	set_img();
}

function flashLogo() {
	var deng = document.getElementById("shanshuo");
	if(shang == 0) {
		deng.src = "/media/images/lottery/17.gif";
		shang = 1;
	} else {
		deng.src = "/media/images/lottery/16.gif";
		shang = 0;
	}
}

function start() {
	//document.getElementById("startButton").href="javascript:void(null);";
	if (effective.length > 0) {
		document.getElementById("startButton").href="javascript:stop();";
		document.getElementById("startButton_img").src="/media/images/lottery/3.gif";
		set_img_objs();
		Marquee();
		lottery_interval = setInterval(Marquee,speed);
		fla_inter_obj = setInterval(flashLogo, 100);
		//setTimeout("stop()", 3000);
		open_url('/lottery/start/','',true);
	}
	else {
		alert('所有员工都已获奖');
	}
}

function stop() {
	document.getElementById("startButton").href="javascript:start();";
	document.getElementById("startButton_img").src="/media/images/lottery/1.gif";
	clearInterval(fla_inter_obj);
	document.getElementById("shanshuo").src = "/media/images/lottery/17.gif";
	clearInterval(lottery_interval);
	set_number(effective);
	set_img();
	open_url("/lottery/stop/","m="+number,false);
	//Marquee();
	//number = the_msg;
	//set_img();
	//clearInterval(fla_inter_obj);
	//document.getElementById("shanshuo").src = "/media/images/lottery/17.gif";
	//the_msg = "";
}

//设置参数信息
function open_url(url,param,is_async){
	//$.post('/parameters/write_mapdata/',{'mapdata':mapdata},function(data){return data;});
	$.ajax({
		url: url,
		type:'get',
		dataType:'json',
		data:param,
		async:is_async,
		success:visitcallback
	});
	/*if (mapdata != null){
		var mapdata_obj = findObj("idmapdata",document);
		mapdata_obj.value = mapdata;
	}*/
}

//接受返回
function visitcallback(datas)
{	
	//alert(datas);
	var action = datas['action'];
	if (action == 'start'){
		//alert(datas['number']);
		document.getElementById("id_exist_len").innerHTML = datas["prizes_len"];
		document.getElementById("id_prize_img1").src = "";
		document.getElementById("id_prize_intro").innerHTML = "";
	}
	else if (action == 'stop') {
		//the_msg = datas['number'];
		if (datas['code'] == 0) {
			document.getElementById("id_exist_len").innerHTML = datas["prizes_len"];
			document.getElementById("id_prize_img1").src = "/media/"+ datas["prize"].image;
			var intro_html = "<p style='font-family: \"Trebuchet MS\", Arial, \"宋体\"; font-size:18px; text-align:center; color:#000;'>";
			//intro_html += "恭喜【<span style='font-size:36px; text-align:center; color:#FC0;'>"+ datas['name'] +"</span>】获得【<span style='font-size:36px; text-align:center; color:#FC0;'>"+ datas['prize'].name +"</span>】!</p>";
			intro_html += "恭喜！获得【<span style='font-size:36px; text-align:center; color:#FC0;'>"+ datas['prize'].name +"</span>】!</p>";
			intro_html += "<p>&nbsp;&nbsp;"+ datas['prize'].intro +"</p>";
			document.getElementById("id_prize_intro").innerHTML = intro_html;
			//effective.del(index);
			//alert(index);
			effective.remove(index);
			//alert(effective.length);
		}
		else{
			document.getElementById("id_exist_len").innerHTML = datas["prizes_len"];
			document.getElementById("id_prize_img1").src = "";
			document.getElementById("id_prize_intro").innerHTML = "";
			alert(datas['tips']);
		}
	}
	//else if (action == 'fsa') {
	//	fsa_obj.innerHTML = datas["fsa"];
	//}
	//return datas;
}

function fsa(){
	open_url("/lottery/fsa/","",true);
}

//公告定时器
//var fsa_interval = setInterval(fsa,2000);