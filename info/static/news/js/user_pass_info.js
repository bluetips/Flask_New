function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}


$(function () {
    $(".pass_info").submit(function (e) {
        e.preventDefault();

        var params = {};
        $(this).serializeArray().map(function (x) {
            params[x.name] = x.value;
        });

        var npwd_1 = params["npwd_1"];
        var npwd_2 = params["npwd_2"];

        if (npwd_1 != npwd_2) {
            alert('两次密码输入不一致')
            return
        }

        var opwd = $()

        //修改密码
        $.ajax({
            url: "/user/pass_info",
            type: "post",
            contentType: "application/json",
            headers: {
                "X-CSRFToken": getCookie("csrf_token")
            },
            data: JSON.stringify(params),
            success: function (resp) {
                if (resp.errno == "0") {
                    // 修改成功
                    alert("修改成功")
                    window.location.reload()
                } else {
                    alert(resp.errmsg)
                }
            }
        })
    })
})