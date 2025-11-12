export default {
  mounted(el, binding, vnode) {
    console.log("vnode.appContext.config.globalProperties", vnode.appContext);
    const route = vnode.appContext.config.globalProperties.$route;
    if (!route) return;

    const pathSegments = route.path.split("/").filter(Boolean);
    const parentRoute = pathSegments.length > 0 ? pathSegments[0] : "default";

    el.setAttribute("data-test", `${parentRoute}-${binding.value}`);
  },
};
