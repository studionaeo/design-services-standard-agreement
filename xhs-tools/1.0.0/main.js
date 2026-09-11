/* 设计服务标准协议书 · 如实渲染全文(ES2017 / 经典脚本) */
(function () {
  'use strict';

  var DATA = window.AGREEMENT_DATA;

  function esc(s) {
    return String(s)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');
  }

  /* 正文按原文显示，仅转义 HTML 字符 */
  function fmt(s) {
    return esc(s);
  }

  /* ---------- 目录(按 md 目录清单收录及缩进) ---------- */
  function targetAttrs(entry) {
    return ' data-chapter="' + entry.ch + '" data-target="' + esc(entry.target) + '"';
  }

  function topClearance() {
    return parseFloat(window.getComputedStyle(document.getElementById('doc-body')).paddingTop) || 52;
  }

  function jumpFrom(el0, bound) {
    var t = el0;
    while (t && t !== bound) {
      if (t.getAttribute) {
        var ch = t.getAttribute('data-chapter');
        if (ch) {
          var id = t.getAttribute('data-target');
          var target = document.getElementById(id);
          if (target) {
            var top = Math.max(0, window.pageYOffset + target.getBoundingClientRect().top - topClearance());
            if ('scrollBehavior' in document.documentElement.style) {
              window.scrollTo({ top: top, behavior: 'smooth' });
            } else {
              window.scrollTo(0, top);
            }
            return true;
          }
        }
      }
      t = t.parentNode;
    }
    return false;
  }

  var tocHtml = '';
  for (var i = 0; i < DATA.toc.length; i++) {
    var entry = DATA.toc[i];
    tocHtml += '<li class="toc-item"' + targetAttrs(entry) + '>' +
      '<span class="toc-no">' + esc(entry.num) + '</span>' +
      '<span class="toc-main">' +
      '<div class="toc-cn">' + esc(entry.cn) + '</div>';
    for (var s = 0; s < entry.subs.length; s++) {
      tocHtml += '<div class="toc-sub lvl' + entry.subs[s].lvl + '"' + targetAttrs(entry.subs[s]) + '>' + esc(entry.subs[s].cn) + '</div>';
    }
    tocHtml += '</span></li>';
  }
  /* ---------- 正文(目录按 md 顺序插在"使用指南"之后) ---------- */
  function renderTable(rows) {
    var html = '<table class="sig-table">';
    for (var r = 0; r < rows.length; r++) {
      html += '<tr>';
      for (var c = 0; c < rows[r].length; c++) {
        html += '<td>' + rows[r][c].map(esc).join('<br>') + '</td>';
      }
      html += '</tr>';
    }
    return html + '</table>';
  }

  var bodyHtml = '';
  for (var n = 0; n < DATA.chapters.length; n++) {
    if (n === 1) {
      bodyHtml += '<section class="chapter doc-toc" id="doc-toc">' +
        '<div class="toc-head-cn">目录</div>' +
        '<ol class="toc-list" id="toc-list"></ol>' +
        '</section>';
    }
    var chapter = DATA.chapters[n];
    bodyHtml += '<section class="chapter" id="ch-' + n + '">';
    if (chapter.en) {
      bodyHtml += '<h1 class="chapter-title-en">' + esc(chapter.en) + '</h1>';
    }
    bodyHtml += '<h2 class="chapter-title-cn">' + esc(chapter.cn) + '</h2>';

    for (var b = 0; b < chapter.blocks.length; b++) {
      var blk = chapter.blocks[b];
      var blockId = 'ch-' + n + '-b' + b;
      if (/^h[3-6]$/.test(blk.t)) {
        bodyHtml += '<' + blk.t + ' id="' + blockId + '">' + esc(blk.cn) + '</' + blk.t + '>';
      } else if (blk.t === 'ol' || blk.t === 'ul') {
        bodyHtml += '<' + blk.t + ' class="body-list">';
        for (var li = 0; li < blk.items.length; li++) {
          var item = blk.items[li];
          bodyHtml += '<li id="' + blockId + '-i' + li + '"' + (blk.t === 'ol' ? ' value="' + parseInt(item.num, 10) + '"' : '') + '>' + fmt(item.cn) + '</li>';
        }
        bodyHtml += '</' + blk.t + '>';
      } else if (blk.t === 'table') {
        bodyHtml += renderTable(blk.rows);
      } else {
        var m = /^((?:IP)?\d+(?:\.\d+)*\.?)(?:\s+|$)/.exec(blk.cn);
        if (m) {
          bodyHtml += '<p id="' + blockId + '"><span class="clause-num">' + m[1] + '</span> ' + fmt(blk.cn.slice(m[0].length)) + '</p>';
        } else {
          bodyHtml += '<p id="' + blockId + '">' + fmt(blk.cn) + '</p>';
        }
      }
      if (n === 0 && b === 0) {
        bodyHtml += '<p class="download-note">协议开源于 GitHub，完整文件可前往仓库下载：<br>' +
          'https://github.com/studionaeo/design-services-standard-agreement</p>';
      }
    }
    bodyHtml += '</section>';
  }
  document.getElementById('doc-body').innerHTML = bodyHtml;

  /* 目录列表填入 + 点击跳章 */
  var tocList = document.getElementById('toc-list');
  tocList.innerHTML = tocHtml;
  tocList.addEventListener('click', function (e) {
    jumpFrom(e.target, tocList);
  });

  /* ---------- 目录导航:浮动按钮 + 悬浮目录窗 ---------- */
  var fabToc = document.getElementById('fab-toc');
  var tocSheet = document.getElementById('toc-sheet');
  var tocSheetMask = document.getElementById('toc-sheet-mask');
  var tocSheetClose = document.getElementById('toc-sheet-close');
  var tocSheetList = document.getElementById('toc-sheet-list');
  var tocSection = document.querySelector('.doc-toc');
  var chapterEls = [];
  var currentChapter = 0;
  var ci;
  for (ci = 0; ci < DATA.chapters.length; ci++) {
    chapterEls.push(document.getElementById('ch-' + ci));
  }

  var shHtml = '';
  for (ci = 0; ci < DATA.toc.length; ci++) {
    var ent = DATA.toc[ci];
    shHtml += '<li class="toc-sheet-item"' + targetAttrs(ent) + '>' +
      '<span class="ts-no">' + esc(ent.num) + '</span>' +
      '<span class="ts-cn">' + esc(ent.cn) + '</span></li>';
    for (var sj = 0; sj < ent.subs.length; sj++) {
      shHtml += '<li class="ts-sub lvl' + ent.subs[sj].lvl + '"' + targetAttrs(ent.subs[sj]) + '>' + esc(ent.subs[sj].cn) + '</li>';
    }
  }
  tocSheetList.innerHTML = shHtml;

  function openSheet() {
    var items = tocSheetList.children;
    var curEl = null;
    for (var i = 0; i < items.length; i++) {
      items[i].className = items[i].className.replace(/\s*cur/g, '');
      var isChapterRow = items[i].className.indexOf('ts-sub') < 0;
      if (isChapterRow && parseInt(items[i].getAttribute('data-chapter'), 10) === currentChapter) {
        items[i].className += ' cur';
        curEl = items[i];
      }
    }
    tocSheet.className = 'toc-sheet open';
    document.body.style.overflow = 'hidden';
    if (curEl) {
      tocSheetList.scrollTop = curEl.offsetTop - tocSheetList.clientHeight / 2 + curEl.offsetHeight / 2;
    }
  }

  function closeSheet() {
    tocSheet.className = 'toc-sheet';
    document.body.style.overflow = '';
  }

  fabToc.addEventListener('click', openSheet);
  tocSheetMask.addEventListener('click', closeSheet);
  tocSheetClose.addEventListener('click', closeSheet);
  tocSheetList.addEventListener('click', function (e) {
    if (jumpFrom(e.target, tocSheetList)) closeSheet();
  });

  /* 滚动监听:目录出屏则显示浮动按钮,并追踪当前章 */
  var ticking = false;
  function onScroll() {
    if (ticking) return;
    ticking = true;
    window.requestAnimationFrame(function () {
      ticking = false;
      if (tocSection.getBoundingClientRect().bottom < 0) {
        fabToc.className = 'fab-toc show';
      } else {
        fabToc.className = 'fab-toc';
      }
      var cur = 0;
      var threshold = topClearance() + 16;
      for (var i = 0; i < chapterEls.length; i++) {
        if (chapterEls[i].getBoundingClientRect().top <= threshold) cur = i;
      }
      currentChapter = cur;
    });
  }
  window.addEventListener('scroll', onScroll, { passive: true });
})();
