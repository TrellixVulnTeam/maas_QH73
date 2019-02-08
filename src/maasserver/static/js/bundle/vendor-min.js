!function(modules){var installedModules={};function __webpack_require__(moduleId){if(installedModules[moduleId])return installedModules[moduleId].exports;var module=installedModules[moduleId]={i:moduleId,l:!1,exports:{}};return modules[moduleId].call(module.exports,module,module.exports,__webpack_require__),module.l=!0,module.exports}__webpack_require__.m=modules,__webpack_require__.c=installedModules,__webpack_require__.d=function(exports,name,getter){__webpack_require__.o(exports,name)||Object.defineProperty(exports,name,{configurable:!1,enumerable:!0,get:getter})},__webpack_require__.r=function(exports){Object.defineProperty(exports,"__esModule",{value:!0})},__webpack_require__.n=function(module){var getter=module&&module.__esModule?function(){return module.default}:function(){return module};return __webpack_require__.d(getter,"a",getter),getter},__webpack_require__.o=function(object,property){return Object.prototype.hasOwnProperty.call(object,property)},__webpack_require__.p="",__webpack_require__(__webpack_require__.s=0)}({"./src/maasserver/static/js/angular/3rdparty/ng-tags-input.js":function(module,exports){!function(){"use strict";var KEYS_backspace=8,KEYS_tab=9,KEYS_enter=13,KEYS_escape=27,KEYS_space=32,KEYS_up=38,KEYS_down=40,KEYS_left=37,KEYS_right=39,KEYS_delete=46,KEYS_comma=188,SUPPORTED_INPUT_TYPES=["text","email","url"],tagsInput=angular.module("ngTagsInput",[]);tagsInput.directive("tagsInput",["$timeout","$document","$window","tagsInputConfig","tiUtil",function($timeout,$document,$window,tagsInputConfig,tiUtil){function validateType(type){return-1!==SUPPORTED_INPUT_TYPES.indexOf(type)}return{restrict:"E",require:"ngModel",scope:{tags:"=ngModel",onTagAdding:"&",onTagAdded:"&",onInvalidTag:"&",onTagRemoving:"&",onTagRemoved:"&"},replace:!1,transclude:!0,templateUrl:"ngTagsInput/tags-input.html",controller:["$scope","$attrs","$element",function($scope,$attrs,$element){$scope.events=tiUtil.simplePubSub(),tagsInputConfig.load("tagsInput",$scope,$attrs,{template:[String,"ngTagsInput/tag-item.html"],type:[String,"text",validateType],placeholder:[String,"Add a tag"],tabindex:[Number,null],removeTagSymbol:[String,String.fromCharCode(215)],replaceSpacesWithDashes:[Boolean,!0],minLength:[Number,3],maxLength:[Number,9007199254740991],addOnEnter:[Boolean,!0],addOnSpace:[Boolean,!1],addOnComma:[Boolean,!0],addOnBlur:[Boolean,!0],addOnPaste:[Boolean,!1],pasteSplitPattern:[RegExp,/,/],allowedTagsPattern:[RegExp,/.+/],enableEditingLastTag:[Boolean,!1],minTags:[Number,0],maxTags:[Number,9007199254740991],displayProperty:[String,"text"],keyProperty:[String,""],allowLeftoverText:[Boolean,!1],addFromAutocompleteOnly:[Boolean,!1],spellcheck:[Boolean,!0]}),$scope.tagList=new function(options,events,onTagAdding,onTagRemoving){var getTagText,setTagText,tagIsValid,self={};return getTagText=function(tag){return tiUtil.safeToString(tag[options.displayProperty])},setTagText=function(tag,text){tag[options.displayProperty]=text},tagIsValid=function(tag){var tagText=getTagText(tag);return tagText&&tagText.length>=options.minLength&&tagText.length<=options.maxLength&&options.allowedTagsPattern.test(tagText)&&!tiUtil.findInObjectArray(self.items,tag,options.keyProperty||options.displayProperty)&&onTagAdding({$tag:tag})},self.items=[],self.addText=function(text){var tag={};return setTagText(tag,text),self.add(tag)},self.add=function(tag){var tagText=getTagText(tag);return options.replaceSpacesWithDashes&&(tagText=tiUtil.replaceSpacesWithDashes(tagText)),setTagText(tag,tagText),tagIsValid(tag)?(self.items.push(tag),events.trigger("tag-added",{$tag:tag})):tagText&&events.trigger("invalid-tag",{$tag:tag}),tag},self.remove=function(index){var tag=self.items[index];if(onTagRemoving({$tag:tag}))return self.items.splice(index,1),self.clearSelection(),events.trigger("tag-removed",{$tag:tag}),tag},self.select=function(index){index<0?index=self.items.length-1:index>=self.items.length&&(index=0),self.index=index,self.selected=self.items[index]},self.selectPrior=function(){self.select(--self.index)},self.selectNext=function(){self.select(++self.index)},self.removeSelected=function(){return self.remove(self.index)},self.clearSelection=function(){self.selected=null,self.index=-1},self.clearSelection(),self}($scope.options,$scope.events,tiUtil.handleUndefinedResult($scope.onTagAdding,!0),tiUtil.handleUndefinedResult($scope.onTagRemoving,!0)),this.registerAutocomplete=function(){$element.find("input");return{addTag:function(tag){return $scope.tagList.add(tag)},focusInput:function(){},getTags:function(){return $scope.tags},getCurrentTagText:function(){return $scope.newTag.text},getOptions:function(){return $scope.options},on:function(name,handler){return $scope.events.on(name,handler),this}}},this.registerTagItem=function(){return{getOptions:function(){return $scope.options},removeTag:function(index){$scope.disabled||$scope.tagList.remove(index)}}}}],link:function(scope,element,attrs,ngModelCtrl){var setElementValidity,hotkeys=[KEYS_enter,KEYS_comma,KEYS_space,KEYS_backspace,KEYS_delete,KEYS_left,KEYS_right],tagList=scope.tagList,events=scope.events,options=scope.options,input=element.find("input"),validationOptions=["minTags","maxTags","allowLeftoverText"];setElementValidity=function(){ngModelCtrl.$setValidity("maxTags",scope.tags.length<=options.maxTags),ngModelCtrl.$setValidity("minTags",scope.tags.length>=options.minTags),ngModelCtrl.$setValidity("leftoverText",!(!scope.hasFocus&&!options.allowLeftoverText)||!scope.newTag.text)},ngModelCtrl.$isEmpty=function(value){return!value||!value.length},scope.newTag={text:"",invalid:null,setText:function(value){this.text=value,events.trigger("input-change",value)}},scope.track=function(tag){return tag[options.keyProperty||options.displayProperty]},scope.$watch("tags",function(value){scope.tags=tiUtil.makeObjectArray(value,options.displayProperty),tagList.items=scope.tags}),scope.$watch("tags.length",function(){setElementValidity()}),attrs.$observe("disabled",function(value){scope.disabled=value}),scope.eventHandlers={input:{change:function(text){events.trigger("input-change",text)},keydown:function($event){events.trigger("input-keydown",$event)},focus:function(){scope.hasFocus||(scope.hasFocus=!0,events.trigger("input-focus"))},blur:function(){$timeout(function(){var activeElement=$document.prop("activeElement"),lostFocusToBrowserWindow=activeElement===input[0],lostFocusToChildElement=element[0].contains(activeElement);!lostFocusToBrowserWindow&&lostFocusToChildElement||(scope.hasFocus=!1,events.trigger("input-blur"))})},paste:function($event){$event.getTextData=function(){var clipboardData=$event.clipboardData||$event.originalEvent&&$event.originalEvent.clipboardData;return clipboardData?clipboardData.getData("text/plain"):$window.clipboardData.getData("Text")},events.trigger("input-paste",$event)}},host:{click:function(){scope.disabled}}},events.on("tag-added",scope.onTagAdded).on("invalid-tag",scope.onInvalidTag).on("tag-removed",scope.onTagRemoved).on("tag-added",function(){scope.newTag.setText("")}).on("tag-added tag-removed",function(){ngModelCtrl.$setViewValue(scope.tags)}).on("invalid-tag",function(){scope.newTag.invalid=!0}).on("option-change",function(e){-1!==validationOptions.indexOf(e.name)&&setElementValidity()}).on("input-change",function(){tagList.clearSelection(),scope.newTag.invalid=null}).on("input-focus",function(){element.triggerHandler("focus"),ngModelCtrl.$setValidity("leftoverText",!0)}).on("input-blur",function(){options.addOnBlur&&!options.addFromAutocompleteOnly&&tagList.addText(scope.newTag.text),element.triggerHandler("blur"),setElementValidity()}).on("input-keydown",function(event){var shouldAdd,shouldRemove,shouldSelect,shouldEditLastTag,key=event.keyCode,addKeys={};if(!(event.shiftKey||event.altKey||event.ctrlKey||event.metaKey)&&-1!==hotkeys.indexOf(key)){if(addKeys[KEYS_enter]=options.addOnEnter,addKeys[KEYS_comma]=options.addOnComma,addKeys[KEYS_space]=options.addOnSpace,shouldAdd=!options.addFromAutocompleteOnly&&addKeys[key],shouldRemove=(key===KEYS_backspace||key===KEYS_delete)&&tagList.selected,shouldEditLastTag=key===KEYS_backspace&&0===scope.newTag.text.length&&options.enableEditingLastTag,shouldSelect=(key===KEYS_backspace||key===KEYS_left||key===KEYS_right)&&0===scope.newTag.text.length&&!options.enableEditingLastTag,shouldAdd)tagList.addText(scope.newTag.text);else if(shouldEditLastTag){var tag;tagList.selectPrior(),(tag=tagList.removeSelected())&&scope.newTag.setText(tag[options.displayProperty])}else shouldRemove?tagList.removeSelected():shouldSelect&&(key===KEYS_left||key===KEYS_backspace?tagList.selectPrior():key===KEYS_right&&tagList.selectNext());(shouldAdd||shouldSelect||shouldRemove||shouldEditLastTag)&&event.preventDefault()}}).on("input-paste",function(event){if(options.addOnPaste){var tags=event.getTextData().split(options.pasteSplitPattern);tags.length>1&&(tags.forEach(function(tag){tagList.addText(tag)}),event.preventDefault())}})}}}]),tagsInput.directive("tiTagItem",["tiUtil",function(tiUtil){return{restrict:"E",require:"^tagsInput",template:'<ng-include src="$$template"></ng-include>',scope:{data:"="},link:function(scope,element,attrs,tagsInputCtrl){var tagsInput=tagsInputCtrl.registerTagItem(),options=tagsInput.getOptions();scope.$$template=options.template,scope.$$removeTagSymbol=options.removeTagSymbol,scope.$getDisplayText=function(){return tiUtil.safeToString(scope.data[options.displayProperty])},scope.$removeTag=function(){tagsInput.removeTag(scope.$index)},scope.$watch("$parent.$index",function(value){scope.$index=value})}}}]),tagsInput.directive("autoComplete",["$document","$timeout","$sce","$q","tagsInputConfig","tiUtil",function($document,$timeout,$sce,$q,tagsInputConfig,tiUtil){return{restrict:"E",require:"^tagsInput",scope:{source:"&"},templateUrl:"ngTagsInput/auto-complete.html",controller:["$scope","$element","$attrs",function($scope,$element,$attrs){$scope.events=tiUtil.simplePubSub(),tagsInputConfig.load("autoComplete",$scope,$attrs,{template:[String,"ngTagsInput/auto-complete-match.html"],debounceDelay:[Number,100],minLength:[Number,3],highlightMatchedText:[Boolean,!0],maxResultsToShow:[Number,10],loadOnDownArrow:[Boolean,!1],loadOnEmpty:[Boolean,!1],loadOnFocus:[Boolean,!1],selectFirstMatch:[Boolean,!0],displayProperty:[String,""]}),$scope.suggestionList=new function(loadFn,options,events){var getDifference,lastPromise,getTagId,self={};return getTagId=function(){return options.tagsInput.keyProperty||options.tagsInput.displayProperty},getDifference=function(array1,array2){return array1.filter(function(item){return!tiUtil.findInObjectArray(array2,item,getTagId(),function(a,b){return options.tagsInput.replaceSpacesWithDashes&&(a=tiUtil.replaceSpacesWithDashes(a),b=tiUtil.replaceSpacesWithDashes(b)),tiUtil.defaultComparer(a,b)})})},self.reset=function(){lastPromise=null,self.items=[],self.visible=!1,self.index=-1,self.selected=null,self.query=null},self.show=function(){options.selectFirstMatch?self.select(0):self.selected=null,self.visible=!0},self.load=tiUtil.debounce(function(query,tags){self.query=query;var promise=$q.when(loadFn({$query:query}));lastPromise=promise,promise.then(function(items){promise===lastPromise&&(items=tiUtil.makeObjectArray(items.data||items,getTagId()),items=getDifference(items,tags),self.items=items.slice(0,options.maxResultsToShow),self.items.length>0?self.show():self.reset())})},options.debounceDelay),self.selectNext=function(){self.select(++self.index)},self.selectPrior=function(){self.select(--self.index)},self.select=function(index){index<0?index=self.items.length-1:index>=self.items.length&&(index=0),self.index=index,self.selected=self.items[index],events.trigger("suggestion-selected",index)},self.reset(),self}($scope.source,$scope.options,$scope.events),$scope.getCurrentTag=function(){return $scope.$parent.$parent.newTag.text},this.registerAutocompleteMatch=function(){return{getOptions:function(){return $scope.options},getQuery:function(){return $scope.suggestionList.query}}}}],link:function(scope,element,attrs,tagsInputCtrl){var shouldLoadSuggestions,hotkeys=[KEYS_enter,KEYS_tab,KEYS_escape,KEYS_up,KEYS_down],suggestionList=scope.suggestionList,tagsInput=tagsInputCtrl.registerAutocomplete(),options=scope.options,events=scope.events;options.tagsInput=tagsInput.getOptions(),shouldLoadSuggestions=function(value){return value&&value.length>=options.minLength||!value&&options.loadOnEmpty},scope.addSuggestionByIndex=function(index){suggestionList.select(index),scope.addSuggestion()},scope.addSuggestion=function(){var added=!1;return suggestionList.selected&&(tagsInput.addTag(angular.copy(suggestionList.selected)),suggestionList.reset(),tagsInput.focusInput(),added=!0),added},scope.track=function(item){return item[options.tagsInput.keyProperty||options.tagsInput.displayProperty]},tagsInput.on("tag-added invalid-tag input-blur",function(){suggestionList.reset()}).on("input-change",function(value){shouldLoadSuggestions(value)?suggestionList.load(value,tagsInput.getTags()):suggestionList.reset()}).on("input-focus",function(){var value=tagsInput.getCurrentTagText();scope.hasFocus=!0,scope.shouldLoadSuggestions=shouldLoadSuggestions(value),options.loadOnFocus&&scope.shouldLoadSuggestions&&suggestionList.load(value,tagsInput.getTags())}).on("input-keydown",function(event){var key=event.keyCode,handled=!1;if(-1!==hotkeys.indexOf(key))return suggestionList.visible?key===KEYS_down?(suggestionList.selectNext(),handled=!0):key===KEYS_up?(suggestionList.selectPrior(),handled=!0):key===KEYS_escape?(suggestionList.reset(),handled=!0):key!==KEYS_enter&&key!==KEYS_tab||(handled=scope.addSuggestion()):key===KEYS_down&&scope.options.loadOnDownArrow&&(suggestionList.load(tagsInput.getCurrentTagText(),tagsInput.getTags()),handled=!0),handled?(event.preventDefault(),event.stopImmediatePropagation(),!1):void 0}).on("input-blur",function(){scope.hasFocus=!1}),events.on("suggestion-selected",function(index){!function(root,index){var element=root.find("li").eq(index),parent=element.parent(),elementTop=element.prop("offsetTop"),elementHeight=element.prop("offsetHeight"),parentHeight=parent.prop("clientHeight"),parentScrollTop=parent.prop("scrollTop");elementTop<parentScrollTop?parent.prop("scrollTop",elementTop):elementTop+elementHeight>parentHeight+parentScrollTop&&parent.prop("scrollTop",elementTop+elementHeight-parentHeight)}(element,index)})}}}]),tagsInput.directive("tiAutocompleteMatch",["$sce","tiUtil",function($sce,tiUtil){return{restrict:"E",require:"^autoComplete",template:'<ng-include src="$$template"></ng-include>',scope:{data:"="},link:function(scope,element,attrs,autoCompleteCtrl){var autoComplete=autoCompleteCtrl.registerAutocompleteMatch(),options=autoComplete.getOptions();scope.$$template=options.template,scope.$index=scope.$parent.$index,scope.$highlight=function(text){return options.highlightMatchedText&&(text=tiUtil.safeHighlight(text,autoComplete.getQuery())),$sce.trustAsHtml(text)},scope.$getDisplayText=function(){return tiUtil.safeToString(scope.data[options.displayProperty||options.tagsInput.displayProperty])}}}}]),tagsInput.directive("tiTranscludeAppend",function(){return function(scope,element,attrs,ctrl,transcludeFn){transcludeFn(function(clone){element.append(clone)})}}),tagsInput.directive("tiAutosize",["tagsInputConfig",function(tagsInputConfig){return{restrict:"A",require:"ngModel",link:function(scope,element,attrs,ctrl){var span,resize,threshold=tagsInputConfig.getTextAutosizeThreshold();(span=angular.element('<span class="input"></span>')).css("display","none").css("visibility","hidden").css("width","auto").css("white-space","pre"),element.parent().append(span),resize=function(originalValue){var width,value=originalValue;return angular.isString(value)&&0===value.length&&(value=attrs.placeholder),value&&(span.text(value),span.css("display",""),width=span.prop("offsetWidth"),span.css("display","none")),element.css("width",width?width+threshold+"px":""),originalValue},ctrl.$parsers.unshift(resize),ctrl.$formatters.unshift(resize),attrs.$observe("placeholder",function(value){ctrl.$modelValue||resize(value)})}}}]),tagsInput.directive("tiBindAttrs",function(){return function(scope,element,attrs){scope.$watch(attrs.tiBindAttrs,function(value){angular.forEach(value,function(value,key){"type"===key?element[0].type=value:attrs.$set(key,value)})},!0)}}),tagsInput.provider("tagsInputConfig",function(){var globalDefaults={},interpolationStatus={},autosizeThreshold=3;this.setDefaults=function(directive,defaults){return globalDefaults[directive]=defaults,this},this.setActiveInterpolation=function(directive,options){return interpolationStatus[directive]=options,this},this.setTextAutosizeThreshold=function(threshold){return autosizeThreshold=threshold,this},this.$get=["$interpolate",function($interpolate){var converters={};return converters[String]=function(value){return value},converters[Number]=function(value){return parseInt(value,10)},converters[Boolean]=function(value){return"true"===value.toLowerCase()},converters[RegExp]=function(value){return new RegExp(value)},{load:function(directive,scope,attrs,options){var defaultValidator=function(){return!0};scope.options={},angular.forEach(options,function(value,key){var type,localDefault,validator,converter,getDefault,updateValue;type=value[0],localDefault=value[1],validator=value[2]||defaultValidator,converter=converters[type],getDefault=function(){var globalValue=globalDefaults[directive]&&globalDefaults[directive][key];return angular.isDefined(globalValue)?globalValue:localDefault},updateValue=function(value){scope.options[key]=value&&validator(value)?converter(value):getDefault()},interpolationStatus[directive]&&interpolationStatus[directive][key]?attrs.$observe(key,function(value){updateValue(value),scope.events.trigger("option-change",{name:key,newValue:value})}):updateValue(attrs[key]&&$interpolate(attrs[key])(scope.$parent))})},getTextAutosizeThreshold:function(){return autosizeThreshold}}}]}),tagsInput.factory("tiUtil",["$timeout",function($timeout){var self={debounce:function(fn,delay){var timeoutId;return function(){var args=arguments;$timeout.cancel(timeoutId),timeoutId=$timeout(function(){fn.apply(null,args)},delay)}},makeObjectArray:function(array,key){return(array=array||[]).length>0&&!angular.isObject(array[0])&&array.forEach(function(item,index){array[index]={},array[index][key]=item}),array},findInObjectArray:function(array,obj,key,comparer){var item=null;return comparer=comparer||self.defaultComparer,array.some(function(element){if(comparer(element[key],obj[key]))return item=element,!0}),item},defaultComparer:function(a,b){return self.safeToString(a).toLowerCase()===self.safeToString(b).toLowerCase()},safeHighlight:function(str,value){if(!value)return str;str=self.encodeHTML(str),value=self.encodeHTML(value);var expression=new RegExp("&[^;]+;|"+function(str){return str.replace(/([.?*+^$[\]\\(){}|-])/g,"\\$1")}(value),"gi");return str.replace(expression,function(match){return match.toLowerCase()===value.toLowerCase()?"<em>"+match+"</em>":match})},safeToString:function(value){return angular.isUndefined(value)||null==value?"":value.toString().trim()},encodeHTML:function(value){return self.safeToString(value).replace(/&/g,"&amp;").replace(/</g,"&lt;").replace(/>/g,"&gt;")},handleUndefinedResult:function(fn,valueIfUndefined){return function(){var result=fn.apply(null,arguments);return angular.isUndefined(result)?valueIfUndefined:result}},replaceSpacesWithDashes:function(str){return self.safeToString(str).replace(/\s/g,"-")},simplePubSub:function(){var events={};return{on:function(names,handler){return names.split(" ").forEach(function(name){events[name]||(events[name]=[]),events[name].push(handler)}),this},trigger:function(name,args){return(events[name]||[]).every(function(handler){return self.handleUndefinedResult(handler,!0)(args)}),this}}}};return self}]),tagsInput.run(["$templateCache",function($templateCache){$templateCache.put("ngTagsInput/tags-input.html",'<div class="host" tabindex="-1" data-ng-click="eventHandlers.host.click()" ti-transclude-append=""><div class="tags" data-ng-class="{focused: hasFocus}"><ul class="tag-list"><li class="tag-item" data-ng-repeat="tag in tagList.items track by track(tag)" data-ng-class="{ selected: tag == tagList.selected }"><ti-tag-item data="tag"></ti-tag-item></li></ul><input class="input u-no-margin--top u-no-margin--bottom" autocomplete="off" data-ng-model="newTag.text" data-ng-change="eventHandlers.input.change(newTag.text)" data-ng-keydown="eventHandlers.input.keydown($event)" data-ng-focus="eventHandlers.input.focus($event)" data-ng-blur="eventHandlers.input.blur($event)" data-ng-paste="eventHandlers.input.paste($event)" data-ng-trim="false" data-ng-class="{\'invalid-tag\': newTag.invalid}" data-ng-disabled="disabled" ti-bind-attrs="{type: options.type, placeholder: options.placeholder, tabindex: options.tabindex, spellcheck: options.spellcheck}" ti-autosize=""></div></div>'),$templateCache.put("ngTagsInput/tag-item.html",'<span ng-bind="$getDisplayText()"></span> <a class="p-icon--close" data-ng-click="$removeTag()" data-ng-bind="$$removeTagSymbol">Remove tag</a>'),$templateCache.put("ngTagsInput/auto-complete.html",'<div class="autocomplete" data-ng-if="suggestionList.visible"><ul class="p-list suggestion-list"><li class="suggestion-item">Create new tag <span class="tag-item">{$ getCurrentTag() $}</span></li><li class="suggestion-item" data-ng-repeat="item in suggestionList.items track by track(item)" data-ng-class="{selected: item == suggestionList.selected}" data-ng-click="addSuggestionByIndex($index)" data-ng-mouseenter="suggestionList.select($index)"><ti-autocomplete-match data="item"></ti-autocomplete-match></li></ul></div><div class="autocomplete no-suggestion" data-ng-if="!suggestionList.visible && hasFocus && shouldLoadSuggestions"><ul class="p-list suggestion-list"><li class="suggestion-item">Create new tag <span class="tag-item">{$ getCurrentTag() $}</span></li></ul></div>'),$templateCache.put("ngTagsInput/auto-complete-match.html",'<span data-ng-bind-html="$highlight($getDisplayText())"></span>')}])}()},"./src/maasserver/static/js/angular/3rdparty/vs-repeat.js":function(module,exports){!function(window,angular){"use strict";var dde=document.documentElement,matchingFunction=dde.matches?"matches":dde.matchesSelector?"matchesSelector":dde.webkitMatches?"webkitMatches":dde.webkitMatchesSelector?"webkitMatchesSelector":dde.msMatches?"msMatches":dde.msMatchesSelector?"msMatchesSelector":dde.mozMatches?"mozMatches":dde.mozMatchesSelector?"mozMatchesSelector":null,closestElement=angular.element.prototype.closest||function(selector){for(var el=this[0].parentNode;el!==document.documentElement&&null!=el&&!el[matchingFunction](selector);)el=el.parentNode;return el&&el[matchingFunction](selector)?angular.element(el):angular.element()};function getWindowScroll(){if("pageYOffset"in window)return{scrollTop:pageYOffset,scrollLeft:pageXOffset};var sx,d=document,r=d.documentElement,b=d.body;return sx=r.scrollLeft||b.scrollLeft||0,{scrollTop:r.scrollTop||b.scrollTop||0,scrollLeft:sx}}function getClientSize(element,sizeProp){return element===window?"clientWidth"===sizeProp?window.innerWidth:window.innerHeight:element[sizeProp]}var vsRepeatModule=angular.module("vs-repeat",[]).directive("vsRepeat",["$compile","$parse",function($compile,$parse){return{restrict:"A",scope:!0,compile:function($element,$attrs){var ngRepeatExpression,expressionMatches,lhs,rhs,rhsSuffix,originalNgRepeatAttr,repeatContainer=angular.isDefined($attrs.vsRepeatContainer)?angular.element($element[0].querySelector($attrs.vsRepeatContainer)):$element,ngRepeatChild=repeatContainer.children().eq(0),childCloneHtml=ngRepeatChild[0].outerHTML,collectionName="$vs_collection",isNgRepeatStart=!1,attributesDictionary={vsRepeat:"elementSize",vsOffsetBefore:"offsetBefore",vsOffsetAfter:"offsetAfter",vsScrolledToEndOffset:"scrolledToEndOffset",vsScrolledToBeginningOffset:"scrolledToBeginningOffset",vsExcess:"excess",vsScrollMargin:"scrollMargin"};if(ngRepeatChild.attr("ng-repeat"))originalNgRepeatAttr="ng-repeat",ngRepeatExpression=ngRepeatChild.attr("ng-repeat");else if(ngRepeatChild.attr("data-ng-repeat"))originalNgRepeatAttr="data-ng-repeat",ngRepeatExpression=ngRepeatChild.attr("data-ng-repeat");else if(ngRepeatChild.attr("ng-repeat-start"))isNgRepeatStart=!0,originalNgRepeatAttr="ng-repeat-start",ngRepeatExpression=ngRepeatChild.attr("ng-repeat-start");else{if(!ngRepeatChild.attr("data-ng-repeat-start"))throw new Error("angular-vs-repeat: no ng-repeat directive on a child element");isNgRepeatStart=!0,originalNgRepeatAttr="data-ng-repeat-start",ngRepeatExpression=ngRepeatChild.attr("data-ng-repeat-start")}if(expressionMatches=/^\s*(\S+)\s+in\s+([\S\s]+?)(track\s+by\s+\S+)?$/.exec(ngRepeatExpression),lhs=expressionMatches[1],rhs=expressionMatches[2],rhsSuffix=expressionMatches[3],isNgRepeatStart)for(var index=0,repeaterElement=repeatContainer.children().eq(0);null==repeaterElement.attr("ng-repeat-end")&&null==repeaterElement.attr("data-ng-repeat-end");)index++,repeaterElement=repeatContainer.children().eq(index),childCloneHtml+=repeaterElement[0].outerHTML;return repeatContainer.empty(),{pre:function($scope,$element,$attrs){var originalLength,_prevStartIndex,_prevEndIndex,_minStartIndex,_maxEndIndex,_prevClientSize,repeatContainer=angular.isDefined($attrs.vsRepeatContainer)?angular.element($element[0].querySelector($attrs.vsRepeatContainer)):$element,childClone=angular.element(childCloneHtml),childTagName=childClone[0].tagName.toLowerCase(),originalCollection=[],$$horizontal=void 0!==$attrs.vsHorizontal,$beforeContent=angular.element("<"+childTagName+' class="vs-repeat-before-content"></'+childTagName+">"),$afterContent=angular.element("<"+childTagName+' class="vs-repeat-after-content"></'+childTagName+">"),autoSize=!$attrs.vsRepeat,sizesPropertyExists=!!$attrs.vsSize||!!$attrs.vsSizeProperty,$scrollParent=$attrs.vsScrollParent?"window"===$attrs.vsScrollParent?angular.element(window):closestElement.call(repeatContainer,$attrs.vsScrollParent):repeatContainer,$$options="vsOptions"in $attrs?$scope.$eval($attrs.vsOptions):{},clientSize=$$horizontal?"clientWidth":"clientHeight",offsetSize=$$horizontal?"offsetWidth":"offsetHeight",scrollPos=$$horizontal?"scrollLeft":"scrollTop";if($scope.totalSize=0,!("vsSize"in $attrs)&&"vsSizeProperty"in $attrs&&console.warn("vs-size-property attribute is deprecated. Please use vs-size attribute which also accepts angular expressions."),0===$scrollParent.length)throw"Specified scroll parent selector did not match any element";function refresh(){if(!originalCollection||originalCollection.length<1)$scope[collectionName]=[],originalLength=0,$scope.sizesCumulative=[0];else if(originalLength=originalCollection.length,sizesPropertyExists){$scope.sizes=originalCollection.map(function(item){var s=$scope.$new(!1);angular.extend(s,item),s[lhs]=item;var size=$attrs.vsSize||$attrs.vsSizeProperty?s.$eval($attrs.vsSize||$attrs.vsSizeProperty):$scope.elementSize;return s.$destroy(),size});var sum=0;$scope.sizesCumulative=$scope.sizes.map(function(size){var res=sum;return sum+=size,res}),$scope.sizesCumulative.push(sum)}else setAutoSize();reinitialize()}function setAutoSize(){autoSize&&$scope.$$postDigest(function(){if(repeatContainer[0].offsetHeight||repeatContainer[0].offsetWidth){for(var children=repeatContainer.children(),i=0,gotSomething=!1,insideStartEndSequence=!1;i<children.length;){if(null!=children[i].attributes[originalNgRepeatAttr]||insideStartEndSequence){if(gotSomething||($scope.elementSize=0),gotSomething=!0,children[i][offsetSize]&&($scope.elementSize+=children[i][offsetSize]),!isNgRepeatStart)break;if(null!=children[i].attributes["ng-repeat-end"]||null!=children[i].attributes["data-ng-repeat-end"])break;insideStartEndSequence=!0}i++}gotSomething&&(reinitialize(),autoSize=!1,$scope.$root&&!$scope.$root.$$phase&&$scope.$apply())}else var dereg=$scope.$watch(function(){(repeatContainer[0].offsetHeight||repeatContainer[0].offsetWidth)&&(dereg(),setAutoSize())})})}function getLayoutProp(){var layoutPropPrefix="tr"===childTagName?"":"min-";return $$horizontal?layoutPropPrefix+"width":layoutPropPrefix+"height"}function scrollHandler(){if(updateInnerCollection()){$scope.$digest();var expectedSize=sizesPropertyExists?$scope.sizesCumulative[originalLength]:$scope.elementSize*originalLength;expectedSize!==$element[0].clientHeight&&console.warn("vsRepeat: size mismatch. Expected size "+expectedSize+"px whereas actual size is "+$element[0].clientHeight+"px. Fix vsSize on element:",$element[0])}}function onWindowResize(){void 0!==$attrs.vsAutoresize&&(autoSize=!0,setAutoSize(),$scope.$root&&!$scope.$root.$$phase&&$scope.$apply()),updateInnerCollection()&&$scope.$apply()}function reinitialize(){var size;_prevStartIndex=void 0,_prevEndIndex=void 0,_minStartIndex=originalLength,_maxEndIndex=0,size=sizesPropertyExists?$scope.sizesCumulative[originalLength]:$scope.elementSize*originalLength,$scope.totalSize=$scope.offsetBefore+size+$scope.offsetAfter,updateInnerCollection(),$scope.$emit("vsRepeatReinitialized",$scope.startIndex,$scope.endIndex)}function reinitOnClientHeightChange(){var ch=getClientSize($scrollParent[0],clientSize);ch!==_prevClientSize&&(reinitialize(),$scope.$root&&!$scope.$root.$$phase&&$scope.$apply()),_prevClientSize=ch}function updateInnerCollection(){var element,scrollProp,vsElement,scrollElement,isHorizontal,$scrollPosition=(element=$scrollParent[0],scrollProp=scrollPos,element===window?getWindowScroll()[scrollProp]:element[scrollProp]),$clientSize=getClientSize($scrollParent[0],clientSize),scrollOffset=repeatContainer[0]===$scrollParent[0]?0:(vsElement=repeatContainer[0],scrollElement=$scrollParent[0],isHorizontal=$$horizontal,vsElement.getBoundingClientRect()[isHorizontal?"left":"top"]-(scrollElement===window?0:scrollElement.getBoundingClientRect()[isHorizontal?"left":"top"])+(scrollElement===window?getWindowScroll():scrollElement)[isHorizontal?"scrollLeft":"scrollTop"]),__startIndex=$scope.startIndex,__endIndex=$scope.endIndex;if(sizesPropertyExists){for(__startIndex=0;$scope.sizesCumulative[__startIndex]<$scrollPosition-$scope.offsetBefore-scrollOffset-$scope.scrollMargin;)__startIndex++;for(__startIndex>0&&__startIndex--,__endIndex=__startIndex=Math.max(Math.floor(__startIndex-$scope.excess/2),0);$scope.sizesCumulative[__endIndex]<$scrollPosition-$scope.offsetBefore-scrollOffset+$scope.scrollMargin+$clientSize;)__endIndex++;__endIndex=Math.min(Math.ceil(__endIndex+$scope.excess/2),originalLength)}else __startIndex=Math.max(Math.floor(($scrollPosition-$scope.offsetBefore-scrollOffset)/$scope.elementSize)-$scope.excess/2,0),__endIndex=Math.min(__startIndex+Math.ceil($clientSize/$scope.elementSize)+$scope.excess,originalLength);_minStartIndex=Math.min(__startIndex,_minStartIndex),_maxEndIndex=Math.max(__endIndex,_maxEndIndex),$scope.startIndex=$$options.latch?_minStartIndex:__startIndex,$scope.endIndex=$$options.latch?_maxEndIndex:__endIndex,_maxEndIndex<$scope.startIndex&&($scope.startIndex=_maxEndIndex);var digestRequired=!1;if(null==_prevStartIndex?digestRequired=!0:null==_prevEndIndex&&(digestRequired=!0),digestRequired||($$options.hunked?Math.abs($scope.startIndex-_prevStartIndex)>=$scope.excess/2||0===$scope.startIndex&&0!==_prevStartIndex?digestRequired=!0:(Math.abs($scope.endIndex-_prevEndIndex)>=$scope.excess/2||$scope.endIndex===originalLength&&_prevEndIndex!==originalLength)&&(digestRequired=!0):digestRequired=$scope.startIndex!==_prevStartIndex||$scope.endIndex!==_prevEndIndex),digestRequired){var triggerIndex;$scope[collectionName]=originalCollection.slice($scope.startIndex,$scope.endIndex),$scope.$emit("vsRepeatInnerCollectionUpdated",$scope.startIndex,$scope.endIndex,_prevStartIndex,_prevEndIndex),$attrs.vsScrolledToEnd&&(triggerIndex=originalCollection.length-($scope.scrolledToEndOffset||0),($scope.endIndex>=triggerIndex&&_prevEndIndex<triggerIndex||originalCollection.length&&$scope.endIndex===originalCollection.length)&&$scope.$eval($attrs.vsScrolledToEnd)),$attrs.vsScrolledToBeginning&&(triggerIndex=$scope.scrolledToBeginningOffset||0,$scope.startIndex<=triggerIndex&&_prevStartIndex>$scope.startIndex&&$scope.$eval($attrs.vsScrolledToBeginning)),_prevStartIndex=$scope.startIndex,_prevEndIndex=$scope.endIndex;var parsed=$parse(sizesPropertyExists?"(sizesCumulative[$index + startIndex] + offsetBefore)":"(($index + startIndex) * elementSize + offsetBefore)"),o1=parsed($scope,{$index:0}),o2=parsed($scope,{$index:$scope[collectionName].length}),total=$scope.totalSize;$beforeContent.css(getLayoutProp(),o1+"px"),$afterContent.css(getLayoutProp(),total-o2+"px")}return digestRequired}$scope.$scrollParent=$scrollParent,sizesPropertyExists&&($scope.sizesCumulative=[]),$scope.elementSize=+$attrs.vsRepeat||getClientSize($scrollParent[0],clientSize)||50,$scope.offsetBefore=0,$scope.offsetAfter=0,$scope.scrollMargin=0,$scope.excess=2,$$horizontal?($beforeContent.css("height","100%"),$afterContent.css("height","100%")):($beforeContent.css("width","100%"),$afterContent.css("width","100%")),Object.keys(attributesDictionary).forEach(function(key){$attrs[key]&&$attrs.$observe(key,function(value){$scope[attributesDictionary[key]]=+value,reinitialize()})}),$scope.$watchCollection(rhs,function(coll){originalCollection=coll||[],refresh()}),childClone.eq(0).attr(originalNgRepeatAttr,lhs+" in "+collectionName+(rhsSuffix?" "+rhsSuffix:"")),childClone.addClass("vs-repeat-repeated-element"),repeatContainer.append($beforeContent),repeatContainer.append(childClone),$compile(childClone)($scope),repeatContainer.append($afterContent),$scope.startIndex=0,$scope.endIndex=0,$scrollParent.on("scroll",scrollHandler),angular.element(window).on("resize",onWindowResize),$scope.$on("$destroy",function(){angular.element(window).off("resize",onWindowResize),$scrollParent.off("scroll",scrollHandler)}),$scope.$on("vsRepeatTrigger",refresh),$scope.$on("vsRepeatResize",function(){autoSize=!0,setAutoSize()}),$scope.$on("vsRenderAll",function(){$$options.latch&&setTimeout(function(){var __endIndex=originalLength;_maxEndIndex=Math.max(__endIndex,_maxEndIndex),$scope.endIndex=$$options.latch?_maxEndIndex:__endIndex,$scope[collectionName]=originalCollection.slice($scope.startIndex,$scope.endIndex),_prevEndIndex=$scope.endIndex,$scope.$$postDigest(function(){$beforeContent.css(getLayoutProp(),0),$afterContent.css(getLayoutProp(),0)}),$scope.$apply(function(){$scope.$emit("vsRenderAllDone")})})}),$scope.$watch(function(){"function"==typeof window.requestAnimationFrame?window.requestAnimationFrame(reinitOnClientHeightChange):reinitOnClientHeightChange()})}}}}}]);void 0!==module&&module.exports&&(module.exports=vsRepeatModule.name)}(window,window.angular)},0:function(module,exports,__webpack_require__){__webpack_require__("./src/maasserver/static/js/angular/3rdparty/ng-tags-input.js"),module.exports=__webpack_require__("./src/maasserver/static/js/angular/3rdparty/vs-repeat.js")}});
//# sourceMappingURL=vendor-min.js.map