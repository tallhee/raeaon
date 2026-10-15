var _ErrorMap = new JMap();
var _ErrorMessage  = [
  ["USER-1001", "탭에 최대 갯수를 초과하였습니다."],
  ["USER-1002", "로그인이 필요한 서비스입니다."],
  ["USER-1003", "일반 회원을 위한 서비스입니다.."],
  ["USER-1004", "오류가 발생했습니다.관리자에게 문의해 주세요."],
  ["USER-1005", " 방보러가기를 취소 하시겠습니까?"],
  ["USER-1006", "의  방보러가기가 취소되었습니다."],
  ["USER-1007", "아직 게시판이 생성되지 않았습니다."],
  ["USER-1008", "입주민 등록은 일반 회원만 가능합니다."],
  ["USER-1009", "찜하기를  취소 하시겠습니까?"],
  ["USER-1010", "내가 찜한 주택에서 삭제 되었습니다."],
  ["USER-1011", "회원가입을 하시겠습니까?"],
  ["USER-1012", "회원가입이 완료되었습니다."],
  ["USER-1013", "회원정보를 수정하시겠습니까?"],
  ["USER-1014", "회원정보 수정이 완료되었습니다."],
  ["USER-1015", "자신이 작성한 글만 확인할 수 있습니다."],
  
  /*입주민 등록 확인 결과 메시지*/
  ["USER-1020", "#{1} 등록 가능합니다."],
  ["USER-1021", "회원님은 #{1} #{2} #{3} #{4}동 #{5}호에 이미 #{6}으로 등록되어 있습니다."],
  ["USER-1022", "회원님은 #{1} #{2} #{3}에 이미 #{4}으로 등록되어 있습니다."],
  ["USER-1023", "다른 회원이 #{1} #{2} #{3} #{4}동 #{5}호에 이미 등록되어 있습니다. 관리사무소에(#{6}) 문의하여 기존에 등록된 회원의 사용여부를 'N'으로 변경 요청해주세요."],
  ["USER-1024", "다른 회원이 #{1} #{2} #{3}에 이미 #{4}으로 등록되어 있습니다. 관리사무소에(#{5}) 문의하여 기존에 등록된 회원의 사용여부를 'N'으로 변경 요청해주세요."],
  ["USER-1025", "등록가능한 입주민 정보가 없습니다. 관리사무소에(#{1}) 문의 하여 입주민 사전정보 등록 요청하신 후 입주민 등록해주세요."],
  ["USER-1026", "회원님은 #{1} 권한을 가지고 있으므로 #{2} 권한으로 등록할 수 없습니다."],
  ["USER-1027", "회원님은 #{1} #{2} #{3}에 이미 #{4} 권한으로 등록되어 있습니다. 마이페이지의 내 입주/관리 아파트 메뉴에서 사용중지 후 신청하시기 바랍니다."],
  
  ["USER-2001", "[#{1}]을(를) 입력해 주세요"], 
  ["USER-2003", "원하시는 행을 먼저 선택하시기 바랍니다."],
  ["USER-2005", "[#{1}] 이내로 입력 가능합니다."],
  ["USER-2008", "선택된 행이 너무 많습니다."], 
  ["USER-2009", "[#{1}] 등록되어있습니다."],
  ["USER-2010", "한개의 행만 선택해주세요."],
  ["USER-2012", "숫자형식만 입력 가능합니다."], 
  ["USER-2013", "[#{1}] 숫자형식만 입력 가능합니다."],   
  ["USER-2027", "한글은 입력할수 없습니다."],
  ["USER-2028", "[#{1}](이)가 선택되지 않았습니다"],
  ["USER-2029", "입력값이 최대 입력값 보다 큽니다. 최대 입력값 [#{1}]"],
  ["USER-2030", "검색어는 두글자 이상 넣어주세요"],
  ["USER-2031", "[#{1}] 입력해 주세요"], 
  ["USER-2032", "[#{1}] (#{2} ~ #{3})자 이내로 입력해 주세요"],
  ["USER-2033", "[#{1}] 대문자/소문자/숫자/특수문자 중 3가지 이상 조합 되어야 합니다."],  
  ["USER-2034", "[#{1}] 정확히 한번더 입력해 주세요."],
  ["USER-2035", "[#{1}] 다른 비밀번호를 입력해 주세요."],
  ["USER-2036", "[#{1}] (이)가 없습니다."],
  ["USER-2037", "[#{1}] (이)가 다릅니다."],
  ["USER-2038", "먼저 [#{1}] 하세요."],
  ["USER-2039", "[#{1}] 필수입력 항목입니다."],
  ["USER-2040", "일자형식이 맞지 않습니다."],
  ["USER-2041", "시간형식이 맞지 않습니다."], 
  ["USER-2042", "[#{1}]형식만 첨부 가능 합니다."],
  ["USER-2043", "[#{1}]를 확인하세요."],
  ["USER-2044", "[#{1}]e-mail 주소가 잘못된 형태로 입력 되었습니다."],
  ["USER-2045", "[#{1}] #{2} 이상의 숫자만 입력 가능합니다."],
  ["USER-2046", "[#{1}] #{2} 이하의 숫자만 입력 가능합니다."],  
  ["USER-2047", "[#{1}] #{2} 보다 크고 #{3} 보다 작아야 합니다."],    
  ["USER-2048", "[#{1}] 입력값의 길이는 #{2} 이하이어야 합니다."],      
  ["USER-2049", "[#{1}] 입력값의 길이는 #{2} 이상이어야 합니다."],
  ["USER-2050", "[#{1}] 입력값의 길이는 #{2} 이어야 합니다."],  
  ["USER-2051", "[#{1}] 형식이 맞지 않습니다."],
  ["USER-2052", "조회기간은 [#{1}]일 이상일 수 없습니다."],
  ["USER-2053", "시작일자가 종료일자 보다 이후의 날짜입니다."],
  ["USER-2054", "유효한 사업자번호가 아닙니다."],
  ["USER-2055", "유효 범위를 초과하였습니다."],
  
  ["USER-3001", "[#{1}]을(를) 입력해주세요."],   
  ["USER-3002", "첫번째 메뉴를 저장후 추가해주세요."],
  ["USER-3003", "[#{1}]할 대상이 없습니다."],

  ["USER-4001", "[이미 마감횟수 #{1}]회 이상 진행되어 삭제할 수 없습니다."],
  
  ["USER-9000", "세션이 만료 되었습니다.<br>다시 로그인 하여 주세요."],
  ["USER-9001", "저장 하시겠습니까?"], 
  ["USER-9002", "삭제 하시겠습니까?"],
  ["USER-9003", "저장 할 자료가 없습니다."], 
  ["USER-9004", "삭제 할 자료가 없습니다."], 
  ["USER-9008", "[#{1}] 되었습니다."],
  ["USER-9009", "[#{1}] 되지 않았습니다."],
  ["USER-9010", "[#{1}]된 자료는 삭제 할 수 없습니다."],
  ["USER-9011", "선택하신 [#{1}]개 항목을 삭제하시겠습니까"],
  ["USER-9012", "#{1}중 오류가 발생하였습니다.<br>원인:#{2}"],
  ["USER-9013", "선택하신 [#{1}]개 항목을 확정하시겠습니까"],
  ["USER-9014", "선택하신 [#{1}]개 항목을 취소확정하시겠습니까"],
  ["USER-9015", "선택하신 [#{1}]개 항목을 정산월특약 하시겠습니까"],
  ["USER-9016", "선택하신 [#{1}]개 항목의 내용증명을 발행하시겠습니까"],
  ["USER-9017", "선택하신 [#{1}]개 항목에 대해 SMS를 발송하시겠습니까"],
  ["USER-9018", "승인 요청하시겠습니까?"],
  
  ["USER-9031", "#{1} 이미 존재합니다"], 
  ["USER-9032", "저장 할 수 없습니다"],
  ["USER-9033", "데이터(그리드) 영역을 먼저 선택하셔야 합니다"], 
  ["USER-9034", "저장 되었습니다"],
  ["USER-9035", "#{1} 저장 되었습니다"],
  ["USER-9036", "현재 비밀번호가 정확하지 않습니다."],
  ["USER-9037", "비밀번호가 변경되었습니다. <br>로그아웃됩니다.<br>변경된 비밀번호로 로그인 하세요."],
  ["USER-9038", "비밀번호를 생성해 주세요."],
  ["USER-9039", "비밀번호가 초기화 되었습니다."],  
  
  ["USER-9040", "[#{1}] 하시겠습니까?"], 
  ["USER-9041", "[#{1}] 할 자료가 없습니다."],
  ["USER-9042", "이미 [#{1}] 되었습니다."],
  ["USER-9043", "[#{1}] 할 수 없습니다. <br>반복될 경우 관리자에게 문의하세요"],
  ["USER-9044", "[#{1}](을)를 가져 올 수 없습니다. <br>반복될 경우 관리자에게 문의하세요"],
  ["USER-9045", "[#{1}](을)를 확인 할 수 없습니다. <br>반복될 경우 관리자에게 문의하세요"],
  
  ["USER-9051", "데이터를 조회할 수 없습니다.<br>관리자에게 문의하세요."],
  ["USER-9052", "좌측상단의 회사를 선택해주세요."],
  ["USER-9053", "전표가 마감되어서 전표번호를 채번할 수 없습니다."],
  ["USER-9054", "정기예금사용이력이 있으므로 삭제할 수 없습니다."],
  
  ["USER-9061", "하위 데이터가 있어 삭제할 수 없습니다."],
  ["USER-9062", "승인 되었습니다."],
  ["USER-9063", "삭제 되었습니다."],
  
  ["USER-9070", "#{1} 목록으로 가시겠습니까?"],
  
  ["USER-9999", "#{1}"]
  
  ];

_putErrorMessage(_ErrorMessage);

/**
* putErrorMessage
*/
function _putErrorMessage(msgMap) {
  for (var i=0, n=msgMap.length; i<n;i++){

    var key = msgMap[i][0]; //ERROR CODE
    var msg = msgMap[i][1]; //ERROR MESSAGE
    _ErrorMap.put(key, msg);
  }
}

/**
* parsetMessage
*/
function _parseMessage(argKey) {
  var msg = _ErrorMap.get(argKey[0]);
  if (msg == null) {
	  msg = argKey[0];
  }
  for (var i=1, n=argKey.length; i<n; i++) {
    msg = msg.replace(eval("/#{(" + i.toString() + ")}/g"), argKey[i]);
  }
  return msg;
}

/**
* showMessage
*/
function showMessage() {
	var strReturn  = "";
	var strButton  = arguments[0];
	var strMsgCode = arguments[1];					
	var rtn;
	
	if (strMsgCode.indexOf("-") == -1){
		strReturn = 0;
		return strReturn;
	} else {
		var objParseMsg = new Array();
		var strMsg = "";
		
		objParseMsg.push(strMsgCode);
		for(var i=2, n=arguments.length;i<n;i++){
			objParseMsg.push(arguments[i]);
		}
								
		strMsg = _parseMessage(objParseMsg);			
		
		if(strButton.toUpperCase() == "OK") {
			alert_msg(strMsg);
			return;
		} else {
			rtn = confirm_msg(strMsg);
			return rtn;
		}
	}
	
	return strReturn;	
}

/**
* getMessage
*/
function getMessage() {
	var strReturn  = "";
	var strMsgCode  = arguments[0];
	
	
	if (strMsgCode.indexOf("-") == -1){
		return strMsgCode;
	} else {
		var objParseMsg = new Array();
		
		objParseMsg.push(strMsgCode);
		for(var i=1, n=arguments.length;i<n;i++){
			objParseMsg.push(arguments[i]);
		}

		strReturn = _parseMessage(objParseMsg);			

		return strReturn;
	}
	
	return strReturn;	
}


function JMap() {
    
    this._INDEX_KEY = 0;
    this._INDEX_VALUE = 1;
    
    this._elementData = new Array(0);

    this.put = function(key, value) {
        var index = this._findIndexByKey(key);
        if (index >= 0) {
            (this._elementData[index])[this._INDEX_VALUE] = value;
        } else {
            var pair = new Array(2);
            pair[this._INDEX_KEY] = key;
            pair[this._INDEX_VALUE] = value;
            this._elementData.splice(this._elementData.length, 0, pair);
        }
    }
    
    this.get = function(key) {
        var index = this._findIndexByKey(key);
        if (index >= 0) {
            return (this._elementData[index])[this._INDEX_VALUE];
        }
        return null;
    }
    
    this.remove = function(key) {
        var removeIndex = this._findIndexByKey(key);
        if (removeIndex >= 0) {
            this._elementData.splice(removeIndex, 1);
        }
    }

    this.keys = function() {
        var keys = new Array(this._elementData.length);
        for (var i = 0; i < this._elementData.length; i++) {
            keys[i] = (this._elementData[i])[this._INDEX_KEY];
        }
        return keys;
    }
    

    this.values = function() {
        var values = new Array(this._elementData.length);
        for (var i = 0; i < this._elementData.length; i++) {
            values[i] = (this._elementData[i])[this._INDEX_VALUE];
        }
        return values;
    }
    

    this.containsKey = function(key) {
        return (this._findIndexByKey(key) >= 0);
    }
    

    this.isEmpty = function() {
        return (this.size() == 0);
    }
    

    this.clear = function() {
        this._elementData.splice(0, this._elementData.length);
    }
    

    this.size = function() {
        return this._elementData.length;
    }
    

    this.toString = function() {
        var str = "";
        for (var i = 0; i < this._elementData.length; i++) {
            if (i > 0) {
                str += "|";
            }
            str += (this._elementData[i]).join("^");
        }
        return str;
    }
    
    this._findIndexByKey = function(key) {
        if (key == null) {
            throw new JNullPointerException("map's key is null");
        }
        
        for (var i = this._elementData.length - 1; i >= 0; i--) {
            var oldKey = (this._elementData[i])[this._INDEX_KEY];
            if (key == oldKey) {
                return i;
            }
        }
        return -1;
    }
} // End of JMap Class

