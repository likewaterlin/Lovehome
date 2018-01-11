function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function() {
    $("#mobile").focus(function(){
        $("#mobile-err").hide();
    });
    $("#password").focus(function(){
        $("#password-err").hide();
    });
    $(".form-login").submit(function(e){
        e.preventDefault();
        mobile = $("#mobile").val();
        passwd = $("#password").val();
        if (!mobile) {
            $("#mobile-err span").html("请填写正确的手机号！");
            $("#mobile-err").show();
            return;
        } 
        if (!passwd) {
            $("#password-err span").html("请填写密码!");
            $("#password-err").show();
            return;
        }

        //定义数据-->JS对象
        var data = {
            mobile: mobile,
            password: passwd
        };

        //需要转换成JSON对象
        //X-CSRFToken-->固定的写法. 将来对比的时候, 就会从这个Key中取值
        //getCookie: 自己写的从cookie获取cstf_token的方法
        data_json = JSON.stringify(data);
        $.ajax({
            url: "/api/v1_0/sessions", //请求路径URL
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
                    location.href = '/'
                } else {
                    //其他错误, 就弹出提示
                    alert(resp.errmsg)
                }
            }
        });
    });
})