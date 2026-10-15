/*
document.onkeydown = doNotReload;

function doNotReload(){ 
	if( (event.ctrlKey == true && (event.keyCode == 78 || event.keyCode == 82)) //ctrl+N , ctrl+R 
			|| (event.keyCode == 116)){
        event.keyCode = 0; 
        event.cancelBubble = true; 
        event.returnValue = false; 
    } 
}
*/
/** * 중복서브밋 방지

    var doubleSubmitFlag = false;
    function doubleSubmitCheck(){
        if(doubleSubmitFlag){
            return doubleSubmitFlag;
        }else{
            doubleSubmitFlag = true;
            return false;
        }
    }
 
    function insert(){
        if(doubleSubmitCheck()) return;
 
        alert("등록");
    }
 */
var globalMaxFileNum = 10;

// Object.assign not working in internet explorer.
if (typeof Object.assign != 'function') {
	Object.defineProperty(Object, "assign", {
		value: function assign(target, varArgs) { // .length of function is 2
				'use strict';
				if (target == null) { // TypeError if undefined or null
					throw new TypeError('Cannot convert undefined or null to object');
				}
	
				var to = Object(target);
	
				for (var index = 1; index < arguments.length; index++) {
					var nextSource = arguments[index];
					
					if (nextSource != null) { // Skip over if undefined or null
						for (var nextKey in nextSource) {
							if (Object.prototype.hasOwnProperty.call(nextSource, nextKey)) {
								to[nextKey] = nextSource[nextKey];
							}
						}
					}
				}
				return to;
		},
		writable: true,
		configurable: true
	});
}

String.prototype.replaceAll = function(target,replacement){
	return this.split(target).join(replacement);
}
window.onpopstate = function(event) {
	//alert("location: " + document.location + ", state: " + JSON.stringify(event.state));
	location.href=document.location;
}

// onclick 페이지 이동
function onClickLink(url, group, sort){
	console.log("------------- onClickLink group START---------------------------");
	console.log("onClickLink url : "+url);
	console.log("onClickLink group : "+group+", sort : "+sort);
	console.log("------------- onClickLink group END---------------------------");
	location.href=url;
}

// 페이징 처리시 필요한 함수
function pageIndexLink(pageIndex) { 
	onSelect(pageIndex); 
};

function webFilterCheck(formName) {
	if(typeof CKEDITOR != "undefined" && typeof CKEDITOR.instances != "undefined"  && typeof CKEDITOR.instances.nttCn != "undefined" ){
		$("#nttCn").val(CKEDITOR.instances.nttCn.getData());	
	}
	
	var form = $('#'+formName)[0];
	var datas = new FormData(form);
	
//	url : "https://api241.eseoul.go.kr:5443/UPServer/",  -- 금칙어
//	url : "https://api240.eseoul.go.kr:5443/UPServer/", --기존
	$.ajax({
		type : "post",
		enctype: 'multipart/form-data',
		url : "https://api241.eseoul.go.kr:5443/UPServer/",
		data:datas,				
		crossDomain: true,
		contentType: false,
		processData: false,
		success : function(data) {
			webFilterParseResponse(data);
		},
		error : function(data) {
			alert("error");
		}
	});
}

function webFilterParseResponse(json) {
	var responsObj = JSON.parse(json);
	var privacyObj = responsObj.privacy;
	var success = privacyObj[0].isPriv;
	
	var typeCode = ["주민(외국인)번호"	// 1
				   ,"카드번호"			// 2
				   ,"여권번호"			// 3
				   ,"운전면허번호"		// 4  
				   ,"휴대폰번호"		// 5
				   ,"일반전화번호"		// 6
				   ,"이메일"			// 7
				   ,"건강보험번호"		// 8
				   ,"은행계좌번호"		// 9
				   ,"금칙어"			// 10
				   ]
	
	var passPrivType =['2','3','4','6','8','9'];		//typeCode 번호 가져다 놓으면 해당 type은 검출패스
//	var passPrivType =['2','3','4','6','8','9','10'];		//typeCode 번호 가져다 놓으면 해당 type은 검출패스
	
	if(success>0){
		var PrivCnt = 0; 
		var PrivTypeData = privacyObj[0].privType;
		var PrivTypeArr = PrivTypeData.split(",");
		
		var PrivMessage = "검출내용 : ";
		
		for(var i = 0; i<PrivTypeArr.length; i++) {
			if(passPrivType.indexOf(PrivTypeArr[i]) != -1){
				continue;
			}else{
				PrivCnt ++;
				PrivMessage += typeCode[PrivTypeArr[i]-1] ;
			}
			
			if(i+1 != PrivTypeArr.length) {
				PrivMessage += ", "
			}
		}
		
		if ( PrivCnt > 0){
			alert('등록하시려는 내용에 개인정보가 검출되어 등록이 취소되었습니다.\n'+ PrivMessage);
			var funcExist = existFunction("fncFailWebFilter");
			if(funcExist){
				fncFailWebFilter();
			}
			
		} else {
			webFilterAction();
		}
	}else{
		webFilterAction();
	}
	
}

function existFunction(func){
	return typeof window[func]=== "function";
}


function getKaptInfo(targetKind, aptCode) {
	

	$.ajax({
		type : 'POST',
		dataType : 'json',
		url : "/apiLink/getKaptInfo.do",
		data : {
			"targetKind" 	: targetKind,
			"aptCode"		: aptCode
		},
		success : function(data) {
			
			if(data.result == 'true' || data.result == true){
				alert("데이타 갱신에 성공했습니다.");
			}
			else{
				alert("데이타 갱신에 실패했습니다.\n잠시 후 다시 시도 해주세요.");
			}
			
			onSelect();				
		},
		error : function(err) { 
		}, beforeSend: function () {
			if($("#loadingImg").length != 0) {
				$("#loadingImg").show();
			} else {
		        $('#dataCreateWrap').empty();
				$("#dataCreateWrap").append('<div id="loadingImg" style="text-align: center;"><img src="/images/common/loading.gif" style="margin-top:30px; width:150px; height:150px;"  alt="페이지 로딩중"></div>');
			}
       	}, complete: function () {
	       	$("#loadingImg").hide();
       	}
	});
};


// 페이징을 포함해야하는 데이터페이지들 출력하는 함수
function selectList(pageNo, searchParams) {
	if (pageNo == undefined){
		pageNo = 1;
	}
	if(searchParams == undefined || searchParams == "" || searchParams == null){
		searchParams = "";
	}
	
	$.ajax({
		type : 'POST',
		dataType : 'html',
		url : "/commonPortal/selectWithPaging.do",
		data : {
			"query" 		: sel_query,
			"searchValue" 	: searchParams,
			"pageNo" 		: pageNo,
			"returnUrl" 	: returnUrl
		},
		success : function(data) {
			//$('#searchWord').val('');
			$("#dataCreateWrap").html(data);					
		},
		error : function(err) { 
		}, beforeSend: function () {
			if($("#loadingImg").length != 0) {
				$("#loadingImg").show();
			} else {
		        $('#dataCreateWrap').empty();
				$("#dataCreateWrap").append('<div id="loadingImg" style="text-align: center;"><img src="/images/common/loading.gif" style="margin-top:30px; width:150px; height:150px;"  alt="페이지 로딩중"></div>');
			}
       	}, complete: function () {
	       	$("#loadingImg").hide();
       	}
	});
};

// 페이징이 필요없는 데이터페이지들 출력하는 함수
function selectOne(searchParams) {
	$.ajax({
		type : 'POST',
		dataType : 'html',
		url : "/commonPortal/select.do",
		data : {
			"query" 		: sel_query,
			"searchValue" 	: searchParams,
			"returnUrl" 	: returnUrl
		},
		success : function(data) {
			$("#dataCreateWrap").html(data);	
		},
		error : function(err) { 
		}, beforeSend: function () {
			if($("#loadingImg").length != 0) {
				$("#loadingImg").show();
			} else {
		        $('#dataCreateWrap').empty();
				$("#dataCreateWrap").append('<div id="loadingImg" style="text-align: center;"><img src="/images/common/loading.gif" style="margin-top:30px; width:150px; height:150px;"></div>');
			}
       	}, complete: function () {
	       	$("#loadingImg").hide();
       	}
	});
}

//게시판 DETAIL 페이지 호출 함수
function selectDetail(searchParams, historyUrl) { 
	$.ajax({
		type : 'POST',
		dataType : 'html',
		url : "/commonPortal/select.do",
		data : {
			"query" 		: dtl_query,
			"searchValue" 	: searchParams,
			"returnUrl" 	: dtl_returnUrl
		},
		success : function(data) {
			$("#contents").html(data);
			history.pushState(null, null, historyUrl);	// 히스토리 등록
		},
		error : function(err) { 
		}, beforeSend: function () {
			if($("#loadingImg").length != 0) {
				$("#loadingImg").show();
			} else {
		        $('#dataCreateWrap').empty();
				$("#dataCreateWrap").append('<div id="loadingImg" style="text-align: center;"><img src="/images/common/loading.gif" style="margin-top:30px; width:150px; height:150px;"></div>');
			}
       	}, complete: function () {
	       	$("#loadingImg").hide();
       	}
	});
}

// 자치구 선택시 해당 자치구의 법정동 리스트 가져오고, 법정동 선택 시 해당 법정동에 있는 아파트 리스트 가져오는 함수
function commonCodeAjax_gu_dong(gubun, etc){
	var setQuery = null;
	
	var getValue = $("#"+gubun+" option:selected").val();
	if(etc == 'aptInfo.jsp'){
		getValue = $("#"+gubun+" option:selected").text();
	}
	
	var storageGU = localStorage.getItem("storageGU");
 	var storageDONG = localStorage.getItem("storageDONG");
 	var storageAPTCODE = localStorage.getItem("storageAPTCODE");
 	console.log("1storageGU : "+localStorage.getItem("storageGU")+"\nstorageDONG : "+localStorage.getItem("storageDONG")+"\nstorageAPTCODE : "+localStorage.getItem("storageAPTCODE"));

 	if( gubun=="gu" ) {
 		setQuery = "dong";
 		console.log("2storageGU : "+localStorage.getItem("storageGU")+"\nstorageDONG : "+localStorage.getItem("storageDONG")+"\nstorageAPTCODE : "+localStorage.getItem("storageAPTCODE"));
 		
 		if(getValue != "" && etc != 'aptInfo.jsp') {
 			localStorage.clear();
 			localStorage.setItem('storageGU', getValue);
 		} else if(storageGU == "" || storageGU == null || typeof storageGU == "undefined") {
 			localStorage.setItem('storageGU', getValue);
 		} else {
 			getValue = storageGU;
 		}
 	} else if ( gubun=="dong" ) {
 		setQuery = "aptNm";
 		console.log("3storageGU : "+localStorage.getItem("storageGU")+"\nstorageDONG : "+localStorage.getItem("storageDONG")+"\nstorageAPTCODE : "+localStorage.getItem("storageAPTCODE"));
 		
 		if(getValue != "" && etc != 'aptInfo.jsp') {
 			localStorage.removeItem('storageAPTCODE');
 			localStorage.setItem('storageDONG', getValue);
 		} else if(storageDONG == "" || storageDONG == null || typeof storageDONG == "undefined") {
 			localStorage.setItem('storageDONG', getValue);
 		} else {
 			getValue = storageDONG;
 		}
 	} else {
 		localStorageAptCode(gubun);
 	}
	console.log("4storageGU : "+localStorage.getItem("storageGU")+"\nstorageDONG : "+localStorage.getItem("storageDONG")+"\nstorageAPTCODE : "+localStorage.getItem("storageAPTCODE"));

 	var searchValue = "searchValue:" + getValue;
 	$.ajax({
		type : 'POST',
		dataType : 'json',
		url : "/commonPortal/selectCommonCodeAjax.do",
		data : {
			"query" : setQuery,	
			"searchValue" : searchValue
		},
		success : function(data) {
			$("#"+setQuery).empty();
			if(setQuery=="dong") {
				$("#"+setQuery).append("<option value=''>동선택</option>")
				$.each(data['resultData'], function (index, item) { 
					$("#"+setQuery).append("<option value='"+item.adresDong+"'>"+item.adresDong+"</option>")
					if(storageDONG == item.adresDong){
//						$("#"+setQuery+" option:eq("+(index+1)+")").attr("selected", "selected");
					}
					if(etc == 'aptInfo.jsp'){
						selectData();
					}
				});
				$("#aptNm").empty();
				$("#aptNm").append("<option value=''>단지선택</option>");
			} else if(setQuery=="aptNm") {
				$("#"+setQuery).append("<option value=''>단지선택</option>")
				$.each(data['resultData'], function (index, item) { 
					$("#"+setQuery).append("<option value='"+item.aptCode+"'>"+item.aptNm+"</option>")
					if(storageAPTCODE == item.aptCode){
//						$("#"+setQuery+" option:eq("+(index+1)+")").attr("selected", "selected");
					}
				});
			}
		},error : function(err) {}
	}); 	
}

function localStorageAptCode(etc){
	if(etc == "getAptInfo"){
		getAptInfo();
	}
	var aptCode = $("#aptNm option:selected").val();
	
	if(aptCode != ""){
		localStorage.removeItem('storageAPTCODE');
	}
	localStorage.setItem('storageAPTCODE', aptCode);

	$('#aptNm').val(aptCode);
	console.log("5storageGU : "+localStorage.getItem("storageGU")+"\nstorageDONG : "+localStorage.getItem("storageDONG")+"\nstorageAPTCODE : "+localStorage.getItem("storageAPTCODE"));
}
function localStorageAction(){
 	var storageGU = localStorage.getItem("storageGU");
 	var storageDONG = localStorage.getItem("storageDONG");
 	var storageAPTCODE = localStorage.getItem("storageAPTCODE");
 	var storageAPTNM = localStorage.getItem("storageAPTNM");
 	
 	commonCodeAjax_gu_dong("gu");  // 리스트 다시 뽑아 내려고.. 안그럼 선택 한개가 나옴
 	$("#gu").val(storageGU);
 	
	if(storageDONG == "" || storageDONG != null || typeof storageDONG != "undefined"){
		new $.ajax({async: false});
			
 		commonCodeAjax_gu_dong("dong");  // 리스트 다시 뽑아 내려고.. 안그럼 선택 한개가 나옴
	 	$("#dong").val(storageDONG);
 		
	 	if(storageDONG != ""){
		 	$('#aptNm').val(storageAPTCODE);
 		}
	}
}
// 기간 버튼 클릭 시 startDate와 endDate 설정하는 함수
// ex)periodClick(5) = #startDateTx : (현재- 5)달, #endDateTx : 현재 달
function periodClick(gubun) {
	$(".btnSchM").removeClass("on");
	$("#"+gubun+"m").addClass("on");
	
	var date = new Date();
	$("#endDateTx").val(date.getFullYear()+'.'+addZero(date.getMonth()+1));
	date.setMonth(date.getMonth()+1 - gubun);
	$("#startDateTx").val(date.getFullYear()+'.'+addZero(date.getMonth()+1));
};

// 기간 버튼 클릭 시 startDate와 endDate 설정하는 함수
// ex)mgrPeriodClick(5) = #startDateTx : (endDateTx - 5)달, #endDateTx : 현재 달-2
// 관리비는 현재달 기준으로 두달전 내용을 등록해야하니까..
function mgrPeriodClick(gubun) {
	$(".btnSchM").removeClass("on");
	$("#"+gubun+"m").addClass("on");
	
	var date = new Date();
	var yearE = date.getFullYear(); 
	var monthE = date.getMonth()-1;
	if(monthE<1){
		monthE += 12;
		yearE -= 1
	}
	$("#endDateTx").val(yearE+'.'+addZero(monthE));
	
	var yearS = yearE; 
	var monthS = monthE - gubun + 1;
	if(monthS<1){
		monthS += 12;
		yearS -= 1
	}
	$("#startDateTx").val(yearS+'.'+addZero(monthS));
};

// 두자리 미만 숫자 앞에 0 붙히는 함수 
// ex) 1~9 => 01 ~ 09
function addZero(n){
    return n < 10 ? "0" + n: n;
};

//ID가 "searchDate" monthpicker에 두달 전으로 날짜 설정하는 함수
function setMgrDate(){
	var date = new Date(); 
	var year = date.getFullYear(); 
	var month = date.getMonth()-1;
	if(month<1){
		month += 12;
		year -= 1
	}
	$("#searchDate").val(year + "." + addZero(month));
};

//테이블 아코디언
function tableAccordion() {
	$(".infoCostTable tr:not(.accordion)").hide();
	$(".infoCostTable tr.accordion").show();
	$(".infoCostTable tr.accordion").addClass("off");
	$(".infoCostTable tr.tr_show").show();

	/*
	$(".infoCostTable tr.accordion").on("click", function(){
		if ($(this).hasClass("on")) {
			$(this).removeClass("on");
			$(this).addClass("off");
			//$(this).closest("tr td").find('span').text("상세항목열기");
			$(this).closest("tr td span").addClass("txRed");
			alert("333");
		} else {
			$(this).removeClass("off");
			$(this).addClass("on");
			$(this).closest("tr td a span").addClass("txBlue");
			alert("444");
		}
		*/
	$(".infoCostTable tr.accordion a").on("click", function(){
		 if ($(this).closest("tr").hasClass("on")) {
				$(this).closest("tr").removeClass("on");
				$(this).closest("tr").addClass("off");
				$(this).closest("tr td").find('span').text("상세항목열기");
			} else {
				$(this).closest("tr").removeClass("off");
				$(this).closest("tr").addClass("on");
				$(this).closest("tr td").find('span').text("상세항목닫기");
			}
		var tmpStr;

		 if ($(this).closest("tr").hasClass("trItem01")) {
			tmpStr="tr"+".trItem01";
		 }else if ($(this).closest("tr").hasClass("trItem02")) {
			tmpStr="tr"+".trItem02";
		 }else if ($(this).closest("tr").hasClass("trItem03")) {
			tmpStr="tr"+".trItem03";
		 }else if ($(this).closest("tr").hasClass("trItem04")) {
			tmpStr="tr"+".trItem04";
		 }else if ($(this).closest("tr").hasClass("trItem05")) {
			tmpStr="tr"+".trItem05";
		 }else if ($(this).closest("tr").hasClass("trItem06")) {
			tmpStr="tr"+".trItem06";
		 }else if ($(this).closest("tr").hasClass("trItem07")) {
			tmpStr="tr"+".trItem07";
		 }else if ($(this).closest("tr").hasClass("trItem08")) {
			tmpStr="tr"+".trItem08";
		 }else if ($(this).closest("tr").hasClass("trItem09")) {
			tmpStr="tr"+".trItem09";
		 }else if ($(this).closest("tr").hasClass("trItem11")) {
			tmpStr="tr"+".trItem11";
		 }else if ($(this).closest("tr").hasClass("trItem12")) {
			tmpStr="tr"+".trItem12";
		 }else if ($(this).closest("tr").hasClass("trItem13")) {
			tmpStr="tr"+".trItem13";
		 }else if ($(this).closest("tr").hasClass("trItem14")) {
			tmpStr="tr"+".trItem14";
		 }else if ($(this).closest("tr").hasClass("trItem15")) {
			tmpStr="tr"+".trItem15";
		 }
		$(this).closest("tr").nextAll(tmpStr).toggle();
	});
}


function menuCSS(headerMenu, subHeader, SubMenu){
	$("#"+headerMenu).css("color", '#0C82E9 !important');
	$("#"+subHeader).show();
	$("#"+SubMenu).css("color", '#0C82E9 !important');
}

// 데이터 null값 ""로 리턴
function nullString(getStr)
{
	var retStr="";
	if(null == getStr || undefined==getStr) retStr="";
	else retStr = getStr.toString();

	return retStr;
}
// 공통코드로 조회해 와서 select 만들어 주기.
// query : 공통코드 쿼리명
// searchValue : 검색조건
// id : select 의 id 명
// selectedVal : 조회 후 selected 할 value 값
// defVal : 조회랑 관계없이 맨 처음 option 추가할 value 값
// defTxt : 조회랑 관계없이 맨 처음 option 추가할 text 값
// 사용예 : commonCodeAjax("ADMField", "",  "searchField", "${searchParam.searchField}", "", "전체");
function commonCodeAjax(query, searchValue, id, selectedVal, defVal, defTxt){
	$.ajax({
		type : 'POST',
		dataType : 'json',
		url : "/commonPortal/selectCommonCodeAjax.do",
		data : {
			"query" : query,
			"searchValue" : searchValue
		},
		success : function(data) {
			$("#"+id).empty();
			if(nullString(defTxt)!=""){
				$("#"+id).append("<option value='"+defVal+"'>"+defTxt+"</option>");
			}
			$.each(data['resultData'], function(index, item) {
				if(nullString(selectedVal) != "" && selectedVal==item.codeCd){
					$("#"+id).append("<option value='"+item.codeCd+"' selected>"+item.codeNm+"</option>");
				}else{
					$("#"+id).append("<option value='"+item.codeCd+"'>"+item.codeNm+"</option>");
				}
			});
		},
		error : function(err) {
		}
	}); 	
}

function checkDate(argDate){
	var rtn = false;
	argDate = argDate.replace(/[^0-9]/g, '');
	if(argDate.length!=8){
		return rtn;
	}
	argDate = argDate.replace(/([0-9]{4})([0-9]{2})([0-9]{2})/,"$1-$2-$3");
	var adata = argDate.split('-');
	var yyyy = parseInt(adata[0],10);
	var mm = parseInt(adata[1],10);
	var dd = parseInt(adata[2],10);
	var xdata = new Date(yyyy,mm-1,dd);
	if ( ( xdata.getFullYear() === yyyy ) && ( xdata.getMonth () === mm - 1 ) && ( xdata.getDate() === dd ) ) {
		rtn = true;
	}
	return rtn;
}

function getByte_length(str){
	var resultSize = 0;
	if(str == null)
	{
		return 0;
	}
	for(var i=0; i<str.length; i++)
	{
		var c = escape(str.charAt(i));
		if(c.length == 1)
		{
			resultSize ++;
		}
		else if(c.indexOf("%u") != -1)
		{
			resultSize += 2;
		}
		else if(c.indexOf("%") != -1)
		{
			resultSize += c.length/3;
		}
	}
	return resultSize;
}

function fn_nvl(getStr){
	if(getStr == null)
		return "";
	if(getStr=="")
		return "";
	if(typeof getStr == "undefined")
		return "";
	else
		return "";
}

function HTTPS_ON(param){
	//var url = window.location.href;
	var hostname = window.location.hostname;    // localhost
	var host =  window.location.host;			// localhost:6080
	
	if(window.location.href.indexOf('http://') > -1 ){
		if(hostname === "openapt.seoul.go.kr" ){  
			console.log("hostname === openapt.seoul.go.kr");
			window.location.href="https://" + window.location.host + nullString(param); 
		}else{
			console.log("localhost, 211.115.80.235 ~~~~~~~~~~~ PASS");
		}
	}
}

function HTTPS_OFF(param){
	var hostname = window.location.hostname;    // localhost
	var host =  window.location.host;			// localhost:6080
	
	if(window.location.href.indexOf('https://') > -1 ){
		if(hostname === "openapt.seoul.go.kr" ){  
			console.log("hostname === openapt.seoul.go.kr");
			window.location.href="http://" + window.location.host + nullString(param);
		}else{
			console.log("localhost, 211.115.80.235 ~~~~~~~~~~~ PASS");
		}
	}
}

//파일 다운로드
function fileFormDownload(fileId, fileName){
	var $form = $('<form></form>');
	$form.attr("action", "/portal/file/FileDownload.do");
	$form.attr("method", "post");
	$form.attr("target", "_blank");
	$form.appendTo("body");
	$form.append('<input type="hidden" name="CALL_FILE_ID" value="'+fileId+'"/>');
	$form.append('<input type="hidden" name="CALL_FILE_NM" value="'+fileName+'"/>');
	$form.submit();
}

function idCheckPopup(Fg){
	var       url = "/commonPortal/programLink.do?jspNm=include/idChkPopup";
	var    nWidth = "480";
	var   nHeight = "300";
	var      curX = window.screenLeft;
	var      curY = window.screenTop;
	var  curWidth = document.body.clientWidth;
	var curHeight = document.body.clientHeight;
	var     nLeft = curX + (curWidth/2.0) - (nWidth/2.0);
	var      nTop = curY + (curHeight/2.0) - (nHeight/2.0);
	
	var popupOption = "left="  + nLeft + "px, top=" + (nTop-150) + "px," + "width=" + nWidth + "px, height=" + nHeight + "px," + "toolbar=no,menubar=no,location=no, resizable=yes,status=yes"

	var winObj = window.open(url, "reaName", popupOption);
	if (winObj == null) {
	    alert("팝업 차단을 해제해주세요.");
	    return false;
	}
}

function setPhoneNum(rtn){
	var val = rtn.value.replace(/[^0-9]/g, '');
	if(event.keyCode != 12 && event.keyCode != 8) {
		if (getByte_length(val) <= 2) rtn.value = val ;
		if (getByte_length(val) == 3) rtn.value = val + "-";
		if (getByte_length(val) == 4) rtn.value = val.substring(0,3) + "-" + val.substring(3,4) ;
		if (getByte_length(val) == 5) rtn.value = val.substring(0,3) + "-" + val.substring(3,5) ;
		if (getByte_length(val) == 6) rtn.value = val.substring(0,3) + "-" + val.substring(3,6) ;
		if (getByte_length(val) == 7) rtn.value = val.substring(0,3) + "-" + val.substring(3,7) + "-" + val.substring(7,8) ;
		if (getByte_length(val) == 8) rtn.value = val.substring(0,3) + "-" + val.substring(3,7) + "-" + val.substring(7,9) ;
		if (getByte_length(val) == 9) rtn.value = val.substring(0,3) + "-" + val.substring(3,7) + "-" + val.substring(7,10) ;
		if (getByte_length(val) == 10) rtn.value = val.substring(0,3) + "-" + val.substring(3,6) + "-" + val.substring(6,10) ;
		if (getByte_length(val) >= 11) rtn.value = val.substring(0,3) + "-" + val.substring(3,7) + "-" + val.substring(7,11) ;
	}
}

function setNumHyphen(pNum,id){
	if(pNum.length ==10 ){
		pNum = pNum.substring(0,3) + "-" + pNum.substring(3,6) + "-" + pNum.substring(6,10);
	} else if(pNum.length == 11){
		pNum = pNum.substring(0,3) + "-" + pNum.substring(3,7) + "-" + pNum.substring(7,11);
	}
	$('#'+id).val(pNum)
}

function setChangeNum(rtn){
	var val = rtn.value.replace(/[^0-9.]/g, '');
	if(event.keyCode != 12 && event.keyCode != 8) {
		rtn.value = val;
	}
}