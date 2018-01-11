function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(document).ready(function(){

    // 向后端获取城区的信息
    $.get("/api/v1_0/areas", function (resp) {
        if (resp.errno == 0) {
            // 获取到了城区信息
            // var areas = resp.data.areas;
            // for (i=0; i < areas.length; i++){
            //     var area = areas[i];
            //     $("#area-id").append('<option value="'+ area.aid +'">'+ area.aname +'</option>')
            // };

            //1.使用前端模板引擎渲染页面
            //第一个参数: 要渲染的script的id="area-templ
            //第二个参数: 要渲染的数据
            area_html = template("area-templ", {areas:resp.data.areas})


            //2. 设置要渲染的位置
            $("#area-id").html(area_html)

        } else {
            alert(resp.errmsg);
        }
    });

    // 处理房屋基本信息的表单数据
    $("#form-house-info").submit(function (e) {
        e.preventDefault();
        // 检验表单数据是否完整
        // 将表单的数据形成json，向后端发送请求
        var formData = {};
        $(this).serializeArray().map(function (x) { formData[x.name] = x.value });

        // 对于房屋设施的checkbox需要特殊处理
        var facility = [];
        $("input:checkbox:checked[name=facility]").each(function(i, x){ facility[i]=x.value });
        formData.facility = facility;

        // 使用ajax向后端发送请求
        $.ajax({
            url: "/api/v1_0/houses/info",
            type: "post",
            data: JSON.stringify(formData),
            contentType: "application/json",
            dataType: "json",
            headers: {
                "X-CSRFToken": getCookie("csrf_token")
            },
            success: function(resp){
                if ("4101" == resp.errno) {
                    location.href = "/login.html";
                } else if ("0" == resp.errno) {
                    // 后端保存数据成功
                    // 隐藏基本信息的表单
                    $("#form-house-info").hide();
                    // 显示上传图片的表单
                    $("#form-house-image").show();
                    // 设置图片表单对应的房屋编号那个隐藏字段
                    $("#house-id").val(resp.data.house_id);
                } else {
                    alert(resp.errmsg);
                }
            }
        });
    })

    // 处理图片表单的数据
    $("#form-house-image").submit(function (e) {
        e.preventDefault();
        var house_id = $("#house-id").val();
        // 使用jquery.form插件，对表单进行异步提交，通过这样的方式，可以添加自定义的回调函数
        $(this).ajaxSubmit({
            url: "/api/v1_0/houses/"+house_id+"/images",
            type: "post",
            headers: {
                "X-CSRFToken": getCookie("csrf_token")
            },
            success: function (resp) {
                if ("4101" == resp.errno) {
                    location.href = "/login.html";
                } else if ("0" == resp.errno) {
                    // 在前端中添加一个img标签，展示上传的图片
                    $(".house-image-cons").append('<img src="'+ resp.data.image_url+'">');
                } else {
                    alert(resp.errmsg);
                }
            }
        })
    })
})







