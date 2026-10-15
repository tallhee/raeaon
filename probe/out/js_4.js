var windowWidth = getWindowW();
$(document).ready(function()    {


     $('input:checkbox').keypress(function(event) {
         var keycode = (event.keyCode ? event.keyCode : event.which);
         if (keycode == 13) { clickCheckBox(this); }
         event.stopPropagation();
     });


	$('#mydiv').hasClass('foo');
	$('.mainVisual-pause').on('click', function(){$('.flexslider').flexslider('stop');return false;})

	//단지정보 지도검색결과 보이기/숨기기
	$(".btnSHMap").click(function () {
		 if ($(this).hasClass("showSchMap")) {
			$(".schDangiWrap").css({'display':"none"});
			$(".schDangiReList").css({'display':"none"});
			$(".btnSHMap").addClass("hideSchMap");
			$(".btnSHMap").removeClass("showSchMap");
			$(".btnSHMap").html( '<span class=sr-only>결과 보기</span>' );
		 } else {
			$(".schDangiWrap").css({'display':"block"});
			$(".schDangiReList").css({'display':"block"});
			$(".btnSHMap").addClass("showSchMap");
			$(".btnSHMap").removeClass("hideSchMap");
			$(".btnSHMap").html( '<span class=sr-only>결과 숨기기</span>' );
		 }
	})

	//단지정보 지도검색 레이어팝업
	$("#btnSchRe01").click(function () {
		$('.infoDangiFrame').attr('src', "단지정보_기본정보_iframe.html");
		$(".schReLayerWrap").css({'display':"block"});
		$(".schDangiMapWrap").css({'display':"none"});
		$(".btnSHMap").css({'display':"none"});

		$(".schReMenu01").addClass("on");
		$(".schReMenu02").removeClass("on");
		$(".schReMenu03").removeClass("on");
	})
	$("#btnSchRe02").click(function () {
		$('.infoDangiFrame').attr('src', "단지정보_공사용역정보_iframe.html");
		$(".schReLayerWrap").css({'display':"block"});
		$(".schDangiMapWrap").css({'display':"none"});
		$(".btnSHMap").css({'display':"none"});
		$(".schReMenu02").addClass("on");
		$(".schReMenu01").removeClass("on");
		$(".schReMenu01").removeClass("on");
	})
	$("#btnSchRe03").click(function () {
		$('.infoDangiFrame').attr('src', "단지정보_입주자대표회의_iframe.html");
		$(".schReLayerWrap").css({'display':"block"});
		$(".schDangiMapWrap").css({'display':"none"});
		$(".btnSHMap").css({'display':"none"});
		$(".schReMenu03").addClass("on");
		$(".schReMenu01").removeClass("on");
		$(".schReMenu02").removeClass("on");
	})

	//단지정보 지도검색 레이어팝업
	$(".schReMenu01").click(function () {
		$('.infoDangiFrame').attr('src', "단지정보_기본정보_iframe.html");
		$(".schReLayerWrap").css({'display':"block"});
		$(".schDangiMapWrap").css({'display':"none"});
		$(".btnSHMap").css({'display':"none"});
		$(".schReMenu01").addClass("on");
		$(".schReMenu02").removeClass("on");
		$(".schReMenu03").removeClass("on");
	})
	$(".schReMenu02").click(function () {
		$('.infoDangiFrame').attr('src', "단지정보_공사용역정보_iframe.html");
		$(".schReLayerWrap").css({'display':"block"});
		$(".schDangiMapWrap").css({'display':"none"});
		$(".btnSHMap").css({'display':"none"});
		$(".schReMenu02").addClass("on");
		$(".schReMenu01").removeClass("on");
		$(".schReMenu01").removeClass("on");
	})
	$(".schReMenu03").click(function () {
		$('.infoDangiFrame').attr('src', "단지정보_입주자대표회의_iframe.html");
		$(".schReLayerWrap").css({'display':"block"});
		$(".schDangiMapWrap").css({'display':"none"});
		$(".btnSHMap").css({'display':"none"});
		$(".schReMenu03").addClass("on");
		$(".schReMenu01").removeClass("on");
		$(".schReMenu02").removeClass("on");
	})
	$("#btnLayerClose").click(function () {
		$(".schReLayerWrap").css({'display':"none"});
		$(".schDangiMapWrap").css({'display':"block"});
		$(".btnSHMap").css({'display':"none"});
	})

	// 브라우저 창크기 변경시 네비게이션 표시 처리
	$( window ).resize( function() {
		$width = $(window).width();
		if ($width <= 767) {
			$(".sitemapSubMenu").css({'display':"none"});
			$(".sitemapAptSubMenu").css({'display':"none"});
			$(".sitemapAptMngSubMenu").css({'display':"none"});
			$("#bannerWrap").css({'display':"none"});
		} else {
			$(".sitemapSubMenu").css({'display':"block"});
			$(".sitemapAptSubMenu").css({'display':"block"});
			$(".sitemapAptMngSubMenu").css({'display':"block"});
			$("#bannerWrap").css({'display':"block"});
		}
	});

	// 메인네비게이션 - 포털
	// PC 메인네비게이션
	$("#mainGnbNav").mouseover(function(){ openGnb(); });
	$("#mainGnbNav ul li a" ).focus(function(){ openGnb(); });
	$("#headerWrap").mouseleave(function(){ closeGnb(); });
	$("#gnbSitemap").focus(function(){ closeGnb(); });

	// 메인네비게이션 - 포털 - 전체메뉴보기
	$("#gnbSitemap").click(function () {
		$("#sitemapDiv").show();
		$("#sitemapDivBg").show();
		$("body").css('overflow','hidden').css('display','fixed');
		$('#closeSitemapTop').focus();
	});

	// 메인네비게이션 - 포털 - 전체메뉴
	$( ".closeSitemap").click(function() {
		$("body").css({overflow:'auto'})
		$("body").unbind('touchmove');
		$("#sitemapDiv").hide();
		$("#sitemapDivBg").hide();
		$("body").css('overflow','').css('display','');
		$('#gnbSitemap').focus();
	});

	// 메인네비게이션 - 포털 - 모바일 통합검색
	$("#gnbSch").click(function () {
		if (windowWidth <= 767) {
			$("#sitemapDiv").show();
			$("#sitemapDivBg").show();
			$("body").css('overflow','hidden').css('display','fixed');
		}
	})

	// 메인네비게이션 - 포털 - 모바일 네비게이션
	var acc = document.getElementsByClassName("sitemapMenu");
	for (var i = 0; i < acc.length; i++) {
		acc[i].addEventListener("click", function() {
			$width = $(window).width();
			if ($width <= 767) {
				$(".sitemapSubMenu").css({'display':"none"});
				$( '.sitemapMenu' ).removeClass( 'on' );
				this.classList.toggle("on");
				if($("#sitemap .ClassH2").hasClass("on")) {
					var panel = this.nextElementSibling;
					if (panel.style.display === "block") {panel.style.display = "none"
					} else { panel.style.display = "block"; }
				}
			} else { $(".sitemapSubMenu").css({'display':"block"}); }
		});
	}// for


	// 메인네비게이션 - 단지홈
	// PC 메인네비게이션 - 단지홈
	$("#subAptGnbNav").mouseover(function(){ openMenuApt(); });
	$( "#subAptGnbNav ul li a" ).focus(function(){ openMenuApt(); });
	$("#headerAptWrap").mouseleave(function(){ closeMenuApt(); });
	$("#aptSitemap").focus(function(){ closeMenuApt(); });

	// 메인네비게이션 - 단지홈 - 전체메뉴보기
	$("#aptSitemap").click(function () {
		$("#sitemapAptDiv").show();
		$("#sitemapAptDivBg").show();
		$("body").css('overflow','hidden').css('display','fixed');
		$('#closeSitemapAptTop').focus();
	});


	// 메인네비게이션 - 단지홈 - 전체메뉴
	$( ".closeSitemapApt").click(function() {
		$("body").css({overflow:'auto'})
		$("body").unbind('touchmove');
		$("#sitemapAptDiv").hide();
		$("#sitemapAptDivBg").hide();
		$("body").css('overflow','').css('display','');
		$('#aptSitemap').focus();
	});




	// 메인네비게이션 - 단지홈 - 모바일 네비게이션
	var acc = document.getElementsByClassName("sitemapAptMenu");
	for (var i = 0; i < acc.length; i++) {
		acc[i].addEventListener("click", function() {
			$width = $(window).width();
			if ($width <= 767) {
				$(".sitemapAptSubMenu").css({'display':"none"});
				$( '.sitemapAptMenu' ).removeClass( 'on' );
				this.classList.toggle("on");
				if($("#sitemapApt .ClassH2").hasClass("on")) {
					var panel = this.nextElementSibling;
					if (panel.style.display === "block") {panel.style.display = "none"
					} else { panel.style.display = "block"; }
				}
			} else { $(".sitemapAptSubMenu").css({'display':"block"}); }
		});
	}// for

	// 메인네비게이션 - 관리소장
	// PC 메인네비게이션 - 관리소장
	$("#subAptMngGnbNav").mouseover(function(){ openMenuAptMng(); });
	$( "#subAptMngGnbNav ul li a" ).focus(function(){ openMenuAptMng(); });
	$("#headerAptMngWrap").mouseleave(function(){ closeMenuAptMng(); });
	$("#aptMngSitemap").focus(function(){ closeMenuAptMng(); });

	// 메인네비게이션 - 관리소장 - 전체메뉴보기
	$("#aptMngSitemap").click(function () {
		$("#sitemapAptMngDiv").show();
		$("#sitemapAptMngDivBg").show();
		$("body").css('overflow','hidden').css('display','fixed');
		$('#closeSitemapAptMngTop').focus();
	});

	// 메인네비게이션 - 관리소장 - 전체메뉴
	$( ".closeSitemapAptMng").click(function() {
		$("body").css({overflow:'auto'})
		$("body").unbind('touchmove');
		$("#sitemapAptMngDiv").hide();
		$("#sitemapAptMngDivBg").hide();
		$("body").css('overflow','').css('display','');
		$('#aptMngSitemap').focus();
	});

	// 메인네비게이션 - 관리소장 - 모바일 네비게이션
	var acc = document.getElementsByClassName("sitemapAptMngMenu");
	for (var i = 0; i < acc.length; i++) {
		acc[i].addEventListener("click", function() {
			$width = $(window).width();
			if ($width <= 767) {
				$(".sitemapAptMngSubMenu").css({'display':"none"});
				$( '.sitemapAptMngMenu' ).removeClass( 'on' );
				this.classList.toggle("on");
				if($("#sitemapAptMng .ClassH2").hasClass("on")) {
					var panel = this.nextElementSibling;
					if (panel.style.display === "block") {panel.style.display = "none"
					} else { panel.style.display = "block"; }
				}
			} else { $(".sitemapAptMngSubMenu").css({'display':"block"}); }
		});
	}// for

	//FAQ
	var accFAQ = document.getElementsByClassName("faqQ");
	for (var i = 0; i < accFAQ.length; i++) {
		accFAQ[i].addEventListener("click", function() {
			this.classList.toggle("on");
			var panel = this.nextElementSibling;
			if($(".faqQ").hasClass("on")) {
				if (panel.style.display === "block") {panel.style.display = "none"
				} else {panel.style.display = "block";}
			}else {panel.style.display = "none";}
		});
	}// for

	//테이블 아코디언
	$(".infoCostTable tr:not(.accordion)").hide();
	$(".infoCostTable tr.accordion").show();
	$(".infoCostTable tr.accordion").addClass("off");
	$(".infoCostTable tr.tr_show").show();

	$(".infoCostTable tr.accordion a").on("click", function(){
		 if ($(this).closest("tr").hasClass("on")) {
				$(this).closest("tr").removeClass("on");
				$(this).closest("tr").addClass("off");
				$(this).closest("tr td").find('span').text("상세항목 열기");
			} else {
				$(this).closest("tr").removeClass("off");
				$(this).closest("tr").addClass("on");
				$(this).closest("tr td").find('span').text("상세항목 닫기");
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
	//IE에서도 "본문으로 바로가기"가 작동할 수 있도록 이벤트를 설정해줌.
	$("#skipNavi").find("a").eq(0).on("click", function(event){
		event.preventDefault();
		$(location).attr("href", "#container");
		var x = $("#container").find("a");
		if(x.length>0) {x.eq(0).focus();}
	});
	
	if($("#aptCodeIndex").val() != "A10024564"){
		$(".costDetailArea").css({'display':"block"});
	}
	
});

// mainGnb
function openGnb(){
	$("#mainGnbNav ul li ul").slideDown(5);
	$("#mainGnbBg").slideDown(5);
}
function closeGnb(){
	$("#mainGnbNav ul li ul").slideUp(200);
	$("#mainGnbBg").slideUp(200);
}

// 단지홈 메뉴
function openMenuApt(){
	$("#subAptGnbNav ul li ul").slideDown(5);
	$("#subAptGnbBg").slideDown(5);

	if (windowWidth < 1024) {
		$("#aptSitemap").css({'display':"none"});
		$("#aptMenuClose").css({'display':"inline-block"});
	}
}
function closeMenuApt(){
	$("#subAptGnbNav ul li ul").slideUp(200);
	$("#subAptGnbBg").slideUp(200);
	if (windowWidth < 1024) {
		$("#aptMenuClose").css({'display':"none"});
		$("#aptSitemap").css({'display':"inline-block"});
	}
}

// 관리소장홈 메뉴
function openMenuAptMng(){
	$("#subAptMngGnbNav ul li ul").slideDown(5);
	$("#subAptMngGnbBg").slideDown(5);

	if (windowWidth < 1024) {
		$("#aptMngSitemap").css({'display':"none"});
		$("#aptMenuClose").css({'display':"inline-block"});
	}
}
function closeMenuAptMng(){
	$("#subAptMngGnbNav ul li ul").slideUp(200);
	$("#subAptMngGnbBg").slideUp(200);
	if (windowWidth < 1024) {
		$("#aptMenuClose").css({'display':"none"});
		$("#aptMngSitemap").css({'display':"inline-block"});
	}
}

// goTop
function goTop(){
    if ($(this).scrollTop() > 120){
        $(".btn-gotop").stop().fadeIn(200);
    } else{
        $(".btn-gotop").stop().fadeOut(200);
    }
}

//윈도우 가로세로 값구하기
function getWindowW() {
    $width = $(window).width()
	return $width;
}
function getWindowH() {
    $width = $(window).height()
	return $height;
}

$.datepicker.setDefaults({
	closeText: "닫기",
	prevText: "이전달",
	nextText: "다음달",
	currentText: "오늘",
	monthNames: ["1월", "2월", "3월", "4월", "5월", "6월","7월", "8월", "9월", "10월", "11월", "12월"],
	monthNamesShort: ["1월", "2월", "3월", "4월", "5월", "6월","7월", "8월", "9월", "10월", "11월", "12월"],
	dayNames: ["일요일", "월요일", "화요일", "수요일", "목요일", "금요일", "토요일"],
	dayNamesShort: ["일", "월", "화", "수", "목", "금", "토"],
	dayNamesMin: ["일", "월", "화", "수", "목", "금", "토"],
	weekHeader: "주",
	dateFormat: "yy.mm.dd",
	firstDay: 0,
	isRTL: false,
	showMonthAfterYear: true,
	yearSuffix: "년"
})

var currentYear = (new Date()).getFullYear();
var startYear = currentYear-10;
var options = {
   startYear: startYear,
   finalYear: currentYear+1,
   pattern: 'yyyy.mm',
   monthNames: ['1월','2월','3월','4월','5월','6월','7월','8월','9월','10월','11월','12월']
};

function setMonthDefault(gubun) {
	var date = new Date();
	date.setMonth((date.getMonth()-1) - gubun);
	$("#searchDate").val(date.getFullYear()+'.'+addZero(date.getMonth()+1));
};

//체크박스 처리
 function clickCheckBox(box) {
     var $box = $(box);
     $box.prop('checked', !$box.prop('checked'));
 }

function fn_moveMap(target, aptCode, x, y){
	var el = target.id;
	var highlightIcon = new L.icon({iconUrl : _highlightIcon, iconSize : [ 30,34 ], iconAnchor : [ 13, 34 ]})
	$('dl[class=on]').removeClass('on')
	$('.schBtnWrap').css({'display':'none'});
	$(target).addClass('on');
	$('#'+el+ ' .schBtnWrap').css({'display':'block'});
	initMarkerAndLayer()
	map.setView([ y, x ], 15);
	function findMarker(mks){
		return mks.aptCode == aptCode
	}
	var mk = contentMarkers.find(findMarker);
	mk.setIcon(highlightIcon);
}

//숫자 천단위 콤마 추가
function addComma(x) {
	return x.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ",");
}
//숫자 천단위 콤마 제거
function removeComma(x) {
	return x.replace(/[^\d]+/g, '');
}
