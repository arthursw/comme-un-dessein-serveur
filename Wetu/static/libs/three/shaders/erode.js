define([], function() {
	return shader = `
varying vec2 vUv;
uniform vec2 resolution;
uniform sampler2D tDiffuse;

bool isWhiteOrTransparent(vec4 t) {
    return all(greaterThan(t, vec4(0.99))) || t.a < 0.01;
}

void main()	{

	vec4 trgb = texture2D(tDiffuse, vUv);

	bool txm1 = isWhiteOrTransparent(texture2D(tDiffuse, vUv - vec2(1., 0.) / resolution));
	bool tym1 = isWhiteOrTransparent(texture2D(tDiffuse, vUv - vec2(0., 1.) / resolution));
    bool txp1 = isWhiteOrTransparent(texture2D(tDiffuse, vUv + vec2(1., 0.) / resolution));
	bool typ1 = isWhiteOrTransparent(texture2D(tDiffuse, vUv + vec2(0., 1.) / resolution));

	gl_FragColor = txm1 || tym1 || txp1 || typ1 ? vec4(trgb.rgb, 0.0) : trgb;
}`});
