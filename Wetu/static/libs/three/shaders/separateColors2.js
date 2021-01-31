define([], function() {
	return shader = `
varying vec2 vUv;
uniform vec2 resolution;
uniform sampler2D tDiffuse;

bool isWhite(vec4 t) {
    return all(greaterThan(t, vec4(0.99)));
}

bool areEqual(vec4 a, vec4 b) {
    return all( lessThan(abs(a-b), vec4(0.1)) );
}

bool areEqualOrWhite(vec4 a, vec4 b) {
    return areEqual(a, b) || isWhite(a) || isWhite(b);
}

void main()	{
	vec4 t = texture2D(tDiffuse, vUv);
	bool txm1 = areEqualOrWhite(t, texture2D(tDiffuse, vUv - vec2(1., 0.) / resolution));
	bool tym1 = areEqualOrWhite(t, texture2D(tDiffuse, vUv - vec2(0., 1.) / resolution));
	bool txym1 = areEqualOrWhite(t, texture2D(tDiffuse, vUv - vec2(1., 1.) / resolution));
	bool txp1 = areEqualOrWhite(t, texture2D(tDiffuse, vUv + vec2(1., 0.) / resolution));	

	gl_FragColor = txm1 || tym1 || txym1  || txp1 ? vec4(1.0) : t;
}`});
