(function(t){function e(e){for(var o,i,a=e[0],u=e[1],p=e[2],s=0,f=[];s<a.length;s++)i=a[s],Object.prototype.hasOwnProperty.call(r,i)&&r[i]&&f.push(r[i][0]),r[i]=0;for(o in u)Object.prototype.hasOwnProperty.call(u,o)&&(t[o]=u[o]);l&&l(e);while(f.length)f.shift()();return c.push.apply(c,p||[]),n()}function n(){for(var t,e=0;e<c.length;e++){for(var n=c[e],o=!0,a=1;a<n.length;a++){var u=n[a];0!==r[u]&&(o=!1)}o&&(c.splice(e--,1),t=i(i.s=n[0]))}return t}var o={},r={app:0},c=[];function i(e){if(o[e])return o[e].exports;var n=o[e]={i:e,l:!1,exports:{}};return t[e].call(n.exports,n,n.exports,i),n.l=!0,n.exports}i.m=t,i.c=o,i.d=function(t,e,n){i.o(t,e)||Object.defineProperty(t,e,{enumerable:!0,get:n})},i.r=function(t){"undefined"!==typeof Symbol&&Symbol.toStringTag&&Object.defineProperty(t,Symbol.toStringTag,{value:"Module"}),Object.defineProperty(t,"__esModule",{value:!0})},i.t=function(t,e){if(1&e&&(t=i(t)),8&e)return t;if(4&e&&"object"===typeof t&&t&&t.__esModule)return t;var n=Object.create(null);if(i.r(n),Object.defineProperty(n,"default",{enumerable:!0,value:t}),2&e&&"string"!=typeof t)for(var o in t)i.d(n,o,function(e){return t[e]}.bind(null,o));return n},i.n=function(t){var e=t&&t.__esModule?function(){return t["default"]}:function(){return t};return i.d(e,"a",e),e},i.o=function(t,e){return Object.prototype.hasOwnProperty.call(t,e)},i.p="/static/";var a=window["webpackJsonp"]=window["webpackJsonp"]||[],u=a.push.bind(a);a.push=e,a=a.slice();for(var p=0;p<a.length;p++)e(a[p]);var l=u;c.push([0,"chunk-vendors"]),n()})({0:function(t,e,n){t.exports=n("56d7")},"034f":function(t,e,n){"use strict";var o=n("85ec"),r=n.n(o);r.a},"4c76":function(t,e,n){"use strict";var o=n("7313"),r=n.n(o);r.a},"56d7":function(t,e,n){"use strict";n.r(e);n("e260"),n("e6cf"),n("cca6"),n("a79d");var o=n("2b0e"),r=function(){var t=this,e=t.$createElement,n=t._self._c||e;return n("div",{attrs:{id:"app"}},[n("router-view")],1)},c=[],i={name:"App",components:{}},a=i,u=(n("034f"),n("2877")),p=Object(u["a"])(a,r,c,!1,null,null,null),l=p.exports,s=n("8c4f"),f=function(){var t=this,e=t.$createElement,o=t._self._c||e;return o("div",{staticClass:"index"},[o("div",{staticClass:"content"},[t._v(t._s(t.getContent))]),o("figure",{staticStyle:{"margin-top":"80px"}},[o("img",{attrs:{src:n("5d56"),alt:"android",width:"100%"},on:{click:t.jumpToStore}})]),o("figure",{staticStyle:{"margin-top":"10px"}},[o("img",{attrs:{src:n("8a14"),alt:"ios",width:"100%"},on:{click:t.jumpToIosStore}})])])},d=[];n("d3b7"),n("3ca3"),n("ddb0"),n("2b3d");function h(t){return new URL(window.location.href).searchParams.get(t)}var g={name:"HelloWorld",props:{msg:String},data:function(){return{loc:"en"}},mounted:function(){console.log(h("loc")),this.loc=h("loc")},methods:{jumpToStore:function(){window.location.href="https://play.google.com/store/apps/details?id=com.litatom.app"},jumpToIosStore:function(){window.location.href="https://apps.apple.com/us/app/litmatch/id1498889847"}},computed:{getContent:function(){return"TH"===this.loc?"มานี่เจอคนวัยรุ่นและคนแฟชั่น":"VN"===this.loc?"Gặp gỡ các bạn trẻ và thú vị tại đây":"Meet interesting and cool people here"}}},m=g,v=(n("4c76"),Object(u["a"])(m,f,d,!1,null,"621f463b",null)),b=v.exports,w=n("58ca");o["a"].use(s["a"]),o["a"].use(w["a"],{refreshOnceOnNavigation:!0}),o["a"].config.productionTip=!1;var y=new s["a"]({routes:[{path:"/",component:b}]});new o["a"]({render:function(t){return t(l)},router:y}).$mount("#app")},"5d56":function(t,e,n){t.exports=n.p+"img/app_btn.66cfe458.png"},7313:function(t,e,n){},"85ec":function(t,e,n){},"8a14":function(t,e,n){t.exports=n.p+"img/app_btn_ios.c7b6f403.png"}});
//# sourceMappingURL=app.b29ca5dc.js.map