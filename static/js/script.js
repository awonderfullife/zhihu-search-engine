/**
 * Created by Tang Songkai on 1/6/17.
 */

var current_page = -1;
var waiting = false;

function changeValue(obj) {
    document.getElementById('pagelimit-value').innerHTML = '返回' + String(obj.value) + '条数据';
}

function askForResult(page) {

    jQuery('.search-result').empty();

    jQuery('.result-loading-animation').css('display', 'inline');

    var content = document.getElementById('content').value;

    var para = {querys: [], page: 0};

    if (!document.getElementById('checkbox-question').checked) {
        if (document.getElementById('checkbox-question').checked) {
            para['querys'].push({'type': 'question', 'title': content});
        }

        if (document.getElementById('checkbox-answer').checked) {
            para['querys'].push({'type': 'answer', 'text': content});
        }

        if (document.getElementById('checkbox-user').checked) {
            para['querys'].push({'type': 'user', 'description': content});
        }

        if (document.getElementById('checkbox-article').checked) {
            para['querys'].push({'type': 'article', 'text': content});
        }

        if (document.getElementById('checkbox-topic').checked) {
            para['querys'].push({'type': 'topic', 'text': content});
        }
    }
    else {
        para['querys'].push({'raw': content});
    }

    para['page'] = 1;

    var para = {querys: []};

    if (!(document.getElementById('switch-database').checked)) {
        if (document.getElementById('checkbox-question').checked) {
            para['querys'].push({
                'type': 'question',
                'additional': [{'type': 'topic', 'sourcefield': 'tag_indices', 'targetfield': 'index'}],
                'title': content,
                'page': page
            });
        }

        if (document.getElementById('checkbox-answer').checked) {
            para['querys'].push({
                'type': 'answer',
                'additional': [{'type': 'question', 'sourcefield': 'question_index', 'targetfield': 'index'}],
                'text': content,
                'page': page
            });
        }

        if (document.getElementById('checkbox-user').checked) {
            para['querys'].push({
                'type': 'user', 'description': content,
                'page': page
            });
        }

        if (document.getElementById('checkbox-article').checked) {
            para['querys'].push({
                'type': 'article',
                'additional': [{'type': 'topic', 'sourcefield': 'tag_indices', 'targetfield': 'index'}],
                'text': content,
                'page': page
            });
        }

        if (document.getElementById('checkbox-topic').checked) {
            para['querys'].push({
                'type': 'topic',
                'additional': [
                    {'type': 'topic', 'sourcefield': 'index', 'targetfield': 'child_tag_indices'},
                    {'type': 'topic', 'sourcefield': 'child_tag_indices', 'targetfield': 'index'}
                ],
                'text': content,
                'page': page
            });
        }
    }
    else {
        para['querys'].push({'raw': content, 'page': page});
    }

    jQuery.ajax({
            url: '/search',
            data: {data: JSON.stringify(para)},
            type: 'POST',
            dataType: 'json',
            success: function (jsonObj) {
                writeResult(jsonObj, page);
            },
            complete: function (jsonObj) {
                waiting = false;
                jQuery('.result-loading-animation').css('display', 'none');
            }
        }
    )
}


function askForImageResult() {
    jQuery('#content').replaceWith('<form id="form1" method="post"><input type="file" name="keyword" id="_f" /></form> ');
    var form = new FormData(document.getElementById("form1"));
    if (form != null) {
        jQuery.ajax({
            url: '/imgrangesearch',
            type: "post",
            data: form,
            cache: false,
            processData: false,
            contentType: false,
dataType:'json',
            success: function (data) {
                setUpVariousImage(data);
            },
            error: function (e) {
            }
        });
    }

}


function writeResult(jsonObj, page) {
    if (page == 0) {
        jQuery('.search-result').empty();
    }
    for (i = 0; i < jsonObj.results.length; i++) {
        var dataList = jsonObj.results[i].data;
        for (j = 0; j < dataList.length; j++) {
            setUpVariousResultSection(dataList[j]);
        }
    }
    jQuery('img').css('max-width', '600');
    // jQuery('img').each(function(){
    //         this.attr('src','/img?url='+this.attr('src'));
    // });
    var suggestSection = setUpRightSection();
    jQuery('#total-suggest').append(suggestSection);
}

function dateParser(date) {
    var dateStr = String(date);
    return dateStr.substring(0, 4) + '年' + dateStr.substring(4, 6) + '月' + dateStr.substring(6, 8) + '日'
}

function setUpVariousResultSection(dataObj, last) {
    var resultSection;
    var link;
    var description;
    if (dataObj.type == 'article') {
        link = 'https://zhuanlan.zhihu.com/p/' + String(dataObj.index);
        description = dataObj.likes + ' 赞 ' + dateParser(dataObj.date);
        for (var i = 0; i < dataObj.additional[0].length; ++i) {

            if (dataObj.additional[0][i] == null) {
                continue;
            }

            description = description + '<div class="chip">' + dataObj.additional[0][i].text + '</div>';
        }
        resultSection = setUpResultSection('文章', dataObj.title, description, dataObj.text, link, String(dataObj.index));
        jQuery('#article-result').append(resultSection);
    }
    else if (dataObj.type == 'question') {
        link = 'https://www.zhihu.com/question/' + String(dataObj.index);
        description = '';
        for (var i = 0; i < dataObj.additional[0].length; ++i) {
            if (dataObj.additional[0][i] == null) {
                continue;
            }
            description = description + '<div class="chip">' + dataObj.additional[0][i].text + '</div>';
        }
        resultSection = setUpResultSection('问题', dataObj.title, description, dataObj.text, link, String(dataObj.index));
        jQuery('#question-result').append(resultSection);
    }
    else if (dataObj.type == 'answer') {
        link = 'https://www.zhihu.com/answer/' + dataObj.additional[0].title;
        // description = dataObj.author_index + dataObj.likes + ' 赞 ' + dateParser(dataObj.date);
        resultSection = setUpResultSection('答案', dataObj.question_index, description, dataObj.text, link, dataObj.additional[0].title);
        jQuery('#answer-result').append(resultSection);
    }
    else if (dataObj.type == 'user') {
        link = 'https://www.zhihu.com/people/' + String(dataObj.index);
        description = '';
        // var para = {'type': 'topic', 'index': dataObj.followed_topics};


        resultSection = setUpResultSection('用户', dataObj.alias, description, dataObj.description, link, String(dataObj.index));
        jQuery('#user-result').append(resultSection);
    }
    else if (dataObj.type == 'topic') {
        link = 'https://www.zhihu.com/topic/' + String(dataObj.index);
        description = 'father:';

        for (var i = 0; i < dataObj.additional[0].length; ++i) {
            if (dataObj.additional[0][i] == null) {
                continue;
            }
            description = description + '<div class="chip">' + dataObj.additional[0][i].text + '</div>';
        }
        description = description + '\nchildren:';
        for (var i = 0; i < dataObj.additional[1].length; ++i) {
            if (dataObj.additional[1][i] == null) {
                continue;
            }
            description = description + '<div class="chip">' + dataObj.additional[1][i].text + '</div>';
        }
        resultSection = setUpResultSection('话题', dataObj.text, description, 000000, link, String(dataObj.index));
        jQuery('#topic-result').append(resultSection);
    }


    var totalSection = resultSection.clone();
    jQuery('#total-result').append(totalSection);
}

function setUpResultSection(type, title, description, content, link, id) {
    var dataAttr = '';
    if (type == '用户') {
        dataAttr = 'user';
    }
    else if (type == '问题') {
        dataAttr = 'question';
    }
    else if (type == '答案') {
        dataAttr = 'answer';
    }
    else if (type == '话题') {
        dataAttr = 'topic';
    }
    else if (type == '文章') {
        dataAttr = 'article';
    }


    var obj = jQuery('<section class="mdl-grid mdl-grid--no-spacing mdl-shadow--2dp section--left " ' +
        'data-transition="slide" ' +
        'data-type="' + dataAttr + '"' +
        'data-index="' + id +
        '"onmouseover="on_mouse_enter(this)"' +
        'onmouseout="on_mouse_leave(this)">' +
        '<div class="mdl-card mdl-cell mdl-cell--12-col">' +
        '<div class="mdl-card__supporting-text"><h4>' +
        type + '：' + title +
        '</h4>' + description + '<br>' +
        content + '<br>' +
        '</div><div class="mdl-card__actions">' +
        '<a href="' + link +
        '" target ="_blank" class="mdl-button" >Show more</a></div></div>' +
        '<button class="mdl-button mdl-js-button mdl-js-ripple-effect mdl-button--icon" id="" onclick="getUrl(this)">' +
        '<i class="material-icons">share</i></button>' +
        '</section>');

    obj.find('img').each(function () {

        this.src = '/img?url=' + this.src;
    });
    return obj;
}

function setUpRightSection() {
    var sec = jQuery('<div class="demo-card-square mdl-card mdl-shadow--2dp data-display" style="height:90%">' +
        '<div class="mdl-card__title mdl-card--expand"><h2 class="mdl-card__title-text">' +
        'Statistics</h2> </div> <div class="mdl-card__supporting-text">' +
        '<canvas id="data" width="300" height="800" style="width:100%; height:100%"></canvas>'
        + '</div></div>');
    return sec;
}

function setUpVariousImage(jsonObj) {
    jQuery('#image-total-result').empty();
    for (i = 0; i < jsonObj['result'].length; i++) {
        var ImageSection = setUpImage(jsonObj['result'][i][0],jsonObj['result'][i][2]);
        jQuery('#image-total-result').append(ImageSection);
    }
}


function setUpImage(path, link) {
    var imageSection = jQuery('<div class="mdl-cell mdl-cell--4-col"><style>.demo-card-image > .mdl-card__actions ' +
        '{.demo-card-image__filename {color: #fff;font-size: 14px;font-weight: 500;}</style>' +
        '<div class="demo-card-image mdl-card mdl-shadow--2dp" style="background-image:url(' + path +
        ')"><div class="mdl-card__title mdl-card--expand" ></div><div class="mdl-card__actions">' +
        '<span class="demo-card-image__filename"><a href="' + link + '" target="_blank">' +
        link + '</a></span></div></div></div>');

    return imageSection;
}


function mouse_scroll() {
    //兼容完整处理 通过浏览器判断
    var browser = window.navigator.userAgent.toLowerCase().indexOf('firefox');
    if (browser != -1) {
        //处理火狐滚轮事件
        document.addEventListener('DOMMouseScroll', function (ev) {
            var oEvent = ev || event;
            //上下滚轮动作判断
            if (oEvent.detail != 0) {
                check_load_nextpage();
                // check();
            }
        })
    } else {
        //其他浏览器
        document.onmousewheel = function (ev) {
            var oEvent = ev || event;
            //上下滚轮动作判断
            if (oEvent.wheelDelta != 0) {
                check_load_nextpage();
                // check();
            }
        }
    }
}

function on_mouseenter(event) {

}
function on_mouseleave(event) {

}


mouse_scroll();
// }

// jQuery(document).ready(function () {
//     jQuery(window).scroll(function () {
//         var a = document.getElementById("eq").offsetTop;
//         if (a >= jQuery(window).scrollTop() && a < (jQuery(window).scrollTop()+jQuery(window).height())) {
//             alert("233333");
//         }
//     });
// });

function start_loading() {
    if (waiting) {
        return false;
    }
    waiting = true;
    return true;
}
function do_request_search_nosetwait() {
    askForResult(current_page);
}

function do_request_search() {
    if (start_loading()) {
        do_request_search_nosetwait();
    }
}

function on_initialize_new_search(event) {
    if (start_loading()) {
        current_page = 0;
        do_request_search_nosetwait();
    }
}

function get_next_page() {
    if (current_page >= 0) {
        if (start_loading()) {
            ++current_page;
            do_request_search_nosetwait();
        }
    }
}

function check_load_nextpage() {
    // console.log(document.documentElement.scrollTop);
    //
    //
    //
    // var top = document.documentElement.scrollHeight - document.documentElement.clientHeight;
    // if (document.documentElement.scrollTop > top - 100) {
    //     get_next_page();
    // }

    var pic = document.getElementById('total-result').lastChild;
    if (pic.getBoundingClientRect().top < document.documentElement.clientHeight) {
        get_next_page();
    }

}
