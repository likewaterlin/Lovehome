function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
    /*
     1. 正则表达式: ("\\b" + name + "=([^;]*)\\b")

    1.1 \b: 单词边界
    http://www.w3school.com.cn/jsref/jsref_regexp_begin.asp

    1.2 (): 是为了提取匹配的字符串。表达式中有几个()就有几个相应的匹配字符串
    csrt_token=(XXXXX)

    1.3 [^]: 在[]内, 非的意思. 不能以XX进行匹配

    1.4 目前的匹配结果有2个. 一个是整体结果r[0]: csrt_token=(XXXXX)  第二个r[1] : (XXXXX)
    'csrf_token=ImQ5ZTRmMjZ'

    r[0] = csrf_token=ImQ5ZTRmMjZ
    r[1] = ImQ5ZTRmMjZ

    2. 三目运算符, 为了处理简单的if else 而存在的
    if r:
       return r[1]
    else
        return undefined;
     */
}

//因此开始生成发请求, 和后面的获取短信验证码请求. 都需要用到UUID, 所以需要用全局变量来记录
var imageCodeId = "";

function generateUUID() {
    var d = new Date().getTime();
    if(window.performance && typeof window.performance.now === "function"){
        d += performance.now(); //use high-precision timer if available
    }
    var uuid = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
        var r = (d + Math.random()*16)%16 | 0;
        d = Math.floor(d/16);
        return (c=='x' ? r : (r&0x3|0x8)).toString(16);
    });
    return uuid;
}

function generateImageCode() {
    // 1. 生成UUID
     imageCodeId = generateUUID()
    // 2. 给image code的img的src属性, 拼接URL即可
    url = "/api/v1_0/image_codes/" + imageCodeId
    $(".image-code>img").attr("src", url)
}

function sendSMSCode() {
    //移除按钮的点击事件
    $(".phonecode-a").removeAttr("onclick");

    //对数据做判空判断
    var mobile = $("#mobile").val();
    if (!mobile) {
        $("#mobile-err span").html("请填写正确的手机号！");
        $("#mobile-err").show();
        $(".phonecode-a").attr("onclick", "sendSMSCode();");
        return;
    } 
    var imageCode = $("#imagecode").val();
    if (!imageCode) {
        $("#image-code-err span").html("请填写验证码！");
        $("#image-code-err").show();
        $(".phonecode-a").attr("onclick", "sendSMSCode();");
        return;
    }

    //发送get请求
    // 使用ajax方式调用后端接口，发送短信
    var req_data = {
        image_code_id: imageCodeId,
        image_code: imageCode
    };
    $.get("/api/v1_0/sms_codes/" + mobile, req_data, function (resp) {
        // 根据返回的返回数据，进行相应的处理
        if (resp.errno == 4004 || resp.errno == 4002) {
            // 图片验证码的错误
            $("#image-code-err span").html(resp.errmsg);
            $("#image-code-err").show();
            //恢复按钮点击
            $(".phonecode-a").attr("onclick", "sendSMSCode();");
        } else if ( resp.errno == 0 ) {
            // 发送短信成功
            var $time = $(".phonecode-a");
            var duration = 60;
            // 设置定时器
            var intervalid = setInterval(function(){
                $time.html(duration + "秒");
                if(duration === 1){
                    // 清除定时器
                    clearInterval(intervalid);
                    $time.html('获取验证码');
                    $(".phonecode-a").attr("onclick", "sendSMSCode();");
                }
                duration = duration - 1;
            }, 1000, 60);
        } else {
            //理论上应该对各个错误进行针对性处理. 我们这里只是简单的判断了两种错误, 其他错误就直接填出alert提示
            alert(resp.errmsg);
            $(".phonecode-a").attr("onclick", "sendSMSCode();");
        }
    })
}

$(document).ready(function() {
    generateImageCode();
    $("#mobile").focus(function(){
        $("#mobile-err").hide();
    });
    $("#imagecode").focus(function(){
        $("#image-code-err").hide();
    });
    $("#phonecode").focus(function(){
        $("#phone-code-err").hide();
    });
    $("#password").focus(function(){
        $("#password-err").hide();
        $("#password2-err").hide();
    });
    $("#password2").focus(function(){
        $("#password2-err").hide();
    });

    //在提交按钮这里实现post请求的发送
    $(".form-register").submit(function(e){
        //常规post请求点击之后, 会以表单形式发送数据 key=value.
        // 而我们需要用JSON格式去传{"key": "value"}, 所以需要阻止默认的表单提交行为
        e.preventDefault();

        //获取内容, 做简单的判断
        mobile = $("#mobile").val();
        phoneCode = $("#phonecode").val();
        passwd = $("#password").val();
        passwd2 = $("#password2").val();
        if (!mobile) {
            $("#mobile-err span").html("请填写正确的手机号！");
            $("#mobile-err").show();
            return;
        } 
        if (!phoneCode) {
            $("#phone-code-err span").html("请填写短信验证码！");
            $("#phone-code-err").show();
            return;
        }
        if (!passwd) {
            $("#password-err span").html("请填写密码!");
            $("#password-err").show();
            return;
        }
        if (passwd != passwd2) {
            $("#password2-err span").html("两次密码不一致!");
            $("#password2-err").show();
            return;
        }

        //定义数据-->JS对象
        var data = {
            mobile: mobile,
            password: passwd2,
            sms_code: phoneCode
        };

        //需要转换成JSON对象
        //X-CSRFToken-->固定的写法. 将来对比的时候, 就会从这个Key中取值
        //getCookie: 自己写的从cookie获取cstf_token的方法
        data_json = JSON.stringify(data);
        $.ajax({
            url: "/api/v1_0/users", //请求路径URL
            type: "post", //请求方式
            data: data_json, //要发送的数据
            contentType: "application/json", //指明给后端发送的是JSON数据
            dataType: "json", //指明后端给前端的是JSON
            headers: {
              "X-CSRFToken": getCookie('csrf_token')
            },
            success: function (resp) {
                if (resp.errno == 0) {
                    //请求成功, 跳转页面
                    location.href = '/login.html'
                } else {
                    //其他错误, 就弹出提示
                    alert(resp.errmsg)
                }
            }
        });

        //发送post请求
        // $.get $.post 都是ajax的简写.
       /* $.post("/api/v1_0/users", data_json, function (resp) {
            if (resp.errno == 0) {
                //请求成功, 跳转页面
                location.href = '/login.html'
            } else {
                //其他错误, 就弹出提示
                alert(resp.errmsg)
            }
        })*/
    });
})