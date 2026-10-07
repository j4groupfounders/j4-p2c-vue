import fs from "fs";
import { mount, createLocalVue } from "@vue/test-utils";
import VueRouter from "vue-router";
import Vuex from "vuex";
import Errors from "./src/components/ListErrors.vue";
import Pagination from "./src/components/VPagination.vue";
import Footer from "./src/components/TheFooter.vue";
import Header from "./src/components/TheHeader.vue";
const localVue=createLocalVue();localVue.use(VueRouter);localVue.use(Vuex);
test("J4 fixed component HTML and pagination behavior",()=>{
 const router=new VueRouter({routes:[{name:"home",path:"/"},{name:"login",path:"/login"},{name:"register",path:"/register"}]});
 const store=new Vuex.Store({getters:{currentUser:()=>({}),isAuthenticated:()=>false}});
 const opts={localVue,router,store};
 const page=mount(Pagination,{...opts,propsData:{pages:[1,2,3],currentPage:2}});
 page.find('[data-test="page-link-3"]').trigger("click");
 const out={
 errors:mount(Errors,{...opts,propsData:{errors:{title:["required"],body:["too short"]}}}).html(),
 pagination:page.html(),events:page.emitted(),
 footer:mount(Footer,opts).html(),header:mount(Header,opts).html()
 };
 fs.writeFileSync("components.actual.json",JSON.stringify(out,null,2));
 if(fs.existsSync("components.json"))expect(out).toEqual(JSON.parse(fs.readFileSync("components.json","utf8")));
});
