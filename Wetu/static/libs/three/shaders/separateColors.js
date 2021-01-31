define([], function() {
	return shader = `
varying vec2 vUv;
uniform vec2 resolution;
uniform sampler2D tDiffuse;

bool areEqual(vec4 a, vec4 b) {
    return all(lessThan(abs(a-b), vec4(0.1)));
}
void main()	{
	vec4 t = texture2D(tDiffuse, vUv);
	bool txm1 = !areEqual(t, texture2D(tDiffuse, vUv - vec2(1., 0.) / resolution));
	bool tym1 = !areEqual(t, texture2D(tDiffuse, vUv - vec2(0., 1.) / resolution));
	bool txym1 = !areEqual(t, texture2D(tDiffuse, vUv - vec2(1., 1.) / resolution));
	
	gl_FragColor = txm1 || tym1 || txym1 ? vec4(1.0) : t;
}`});
