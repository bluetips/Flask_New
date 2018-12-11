function getCookie(name) {
    var r = document.cookie.match("\\b" + name + "=([^;]*)\\b");
    return r ? r[1] : undefined;
}

$(function () {
    $(".news_review").submit(function (e) {
        e.preventDefault()
        var params = {}
        $(this).serializeArray().map(function (x) {
            params[x.name] = x.value
        })
        var action = params['action']
        var reason = params['reason']
        var news_id = params['news_id']

        params = {
            'action': action,
            'reason': reason,
            'news_id': news_id
        }

        $.ajax({
            url: "/admin/news_review_detail",
            type: "post",
            contentType: "application/json",
            headers: {
                "X-CSRFToken": getCookie("csrf_token")
            },
            data: JSON.stringify(params),
            success: function (resp) {
                if (resp.errno == "0") {
                    // 返回上一页，刷新数据
                    location.href = document.referrer
                } else {
                    alert(resp.errmsg);
                }
            }
        })

    })
})

// 点击取消，返回上一页
function cancel() {
    history.go(-1)
}