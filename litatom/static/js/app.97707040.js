(function(t){function e(e){for(var o,l,a=e[0],c=e[1],p=e[2],s=0,f=[];s<a.length;s++)l=a[s],Object.prototype.hasOwnProperty.call(r,l)&&r[l]&&f.push(r[l][0]),r[l]=0;for(o in c)Object.prototype.hasOwnProperty.call(c,o)&&(t[o]=c[o]);u&&u(e);while(f.length)f.shift()();return i.push.apply(i,p||[]),n()}function n(){for(var t,e=0;e<i.length;e++){for(var n=i[e],o=!0,a=1;a<n.length;a++){var c=n[a];0!==r[c]&&(o=!1)}o&&(i.splice(e--,1),t=l(l.s=n[0]))}return t}var o={},r={app:0},i=[];function l(e){if(o[e])return o[e].exports;var n=o[e]={i:e,l:!1,exports:{}};return t[e].call(n.exports,n,n.exports,l),n.l=!0,n.exports}l.m=t,l.c=o,l.d=function(t,e,n){l.o(t,e)||Object.defineProperty(t,e,{enumerable:!0,get:n})},l.r=function(t){"undefined"!==typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(t,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(t,"__esModule",{value:!0})},l.t=function(t,e){if(1&e&&(t=l(t)),8&e)return t;if(4&e&&"object"===typeof t&&t&&t.__esModule)return t;var n=Object.create(null);if(l.r(n),Object.defineProperty(n,"default",{enumerable:!0,value:t}),2&e&&"string"!=typeof t)for(var o in t)l.d(n,o,function(e){return t[e]}.bind(null,o));return n},l.n=function(t){var e=t&&t.__esModule?function(){return t["default"]}:function(){return t};return l.d(e,"a",e),e},l.o=function(t,e){return Object.prototype.hasOwnProperty.call(t,e)},l.p="/";var a=window["webpackJsonp"]=window["webpackJsonp"]||[],c=a.push.bind(a);a.push=e,a=a.slice();for(var p=0;p<a.length;p++)e(a[p]);var u=c;i.push([0,"chunk-vendors"]),n()})({0:function(t,e,n){t.exports=n("56d7")},"034f":function(t,e,n){"use strict";var o=n("85ec"),r=n.n(o);r.a},"0564":function(t,e,n){t.exports=n.p+"static/img/app_btn_android.66cfe458.png"},"478c":function(t,e,n){t.exports=n.p+"static/img/home_icon.ec5f0a14.png"},"56d7":function(t,e,n){"use strict";n.r(e);n("e623"),n("e379"),n("5dc8"),n("37e1");var o=n("2b0e"),r=function(){var t=this,e=t.$createElement,n=t._self._c||e;return n("div",{attrs:{id:"app"}},[n("HelloWorld")],1)},i=[],l=function(){var t=this,e=t.$createElement,o=t._self._c||e;return o("div",{staticClass:"hello"},[o("el-container",[o("el-main",[o("div",[o("img",{staticClass:"home-icon",attrs:{alt:"Vue logo",src:n("478c")}}),o("div",[o("img",{staticClass:"app-icon",attrs:{alt:"Vue logo",src:n("0564")},on:{click:t.jumpToStore}}),o("img",{staticClass:"app-icon",staticStyle:{"margin-left":"30px"},attrs:{alt:"Vue logo",src:n("8a14")},on:{click:t.jumpToIosStore}})])])]),o("el-footer",[o("div",[o("el-link",{attrs:{underline:!1}},[t._v("Download")]),o("el-link",{staticStyle:{"margin-left":"60px"},attrs:{underline:!1,href:"http://www.litatom.com/api/sns/v1/lit/home/rules"}},[t._v("Terms")])],1)])],1)],1)},a=[],c={name:"HelloWorld",props:{msg:String},methods:{jumpToStore:function(){window.location.href="https://play.google.com/store/apps/details?id=com.litatom.app"},jumpToIosStore:function(){window.location.href="https://apps.apple.com/us/app/litmatch/id1498889847"}}},p=c,u=(n("b7f3"),n("2877")),s=Object(u["a"])(p,l,a,!1,null,"12542e01",null),f=s.exports,d={name:"App",components:{HelloWorld:f}},m=d,g=(n("034f"),Object(u["a"])(m,r,i,!1,null,null,null)),h=g.exports,v=n("5c96"),b=n.n(v);n("0fae");o["default"].use(b.a),o["default"].config.productionTip=!1,new o["default"]({render:function(t){return t(h)}}).$mount("#app")},"85ec":function(t,e,n){},"8a14":function(t,e,n){t.exports=n.p+"static/img/app_btn_ios.c7b6f403.png"},b7f3:function(t,e,n){"use strict";var o=n("c623"),r=n.n(o);r.a},c623:function(t,e,n){}});
//# sourceMappingURL=app.97707040.js.map