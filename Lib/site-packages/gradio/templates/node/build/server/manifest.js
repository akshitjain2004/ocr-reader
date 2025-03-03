const manifest = (() => {
function __memo(fn) {
	let value;
	return () => value ??= (value = fn());
}

return {
	appDir: "_app",
	appPath: "_app",
	assets: new Set([]),
	mimeTypes: {},
	_: {
		client: {"start":"_app/immutable/entry/start.BR5sIYe6.js","app":"_app/immutable/entry/app.Od9--nuV.js","imports":["_app/immutable/entry/start.BR5sIYe6.js","_app/immutable/chunks/client.CYt1WIYP.js","_app/immutable/entry/app.Od9--nuV.js","_app/immutable/chunks/preload-helper.DpQnamwV.js"],"stylesheets":[],"fonts":[],"uses_env_dynamic_public":false},
		nodes: [
			__memo(() => import('./chunks/0-Bp0baKNP.js')),
			__memo(() => import('./chunks/1-BHLXLJlc.js')),
			__memo(() => import('./chunks/2-DpgRF3pD.js').then(function (n) { return n.aI; }))
		],
		routes: [
			{
				id: "/[...catchall]",
				pattern: /^(?:\/(.*))?\/?$/,
				params: [{"name":"catchall","optional":false,"rest":true,"chained":true}],
				page: { layouts: [0,], errors: [1,], leaf: 2 },
				endpoint: null
			}
		],
		matchers: async () => {
			
			return {  };
		},
		server_assets: {}
	}
}
})();

const prerendered = new Set([]);

const base = "";

export { base, manifest, prerendered };
//# sourceMappingURL=manifest.js.map
