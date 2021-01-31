define([], function() {
	return shader = `
varying vec2 vUv;
uniform vec2 resolution;
uniform float stripeWidth;
uniform sampler2D tDiffuse;
// uniform sampler2D tMask;

bool isWhite(vec4 t) {
    return all(greaterThan(t, vec4(0.99)));
}

void main()	{

	// vec4 trgb = texture2D(tDiffuse, vUv);
    // vec4 m = texture2D(tMask, vUv);
    // int nStripes = int(resolution.y / stripeWidth);
    // float sy = vUv.y * float(nStripes);
    // m = fract(sy) > (1.0 / stripeWidth) ? m : vec4(0.0);
    // trgb = isWhite(trgb) ? vec4(1.0) : vec4(0.0);
	// gl_FragColor = m.x > 0.0 ? trgb : vec4(1.0);

	// vec4 trgb = texture2D(tDiffuse, vUv);
    // int nStripes = int(resolution.y / stripeWidth);
    // float sy = vUv.y * float(nStripes);
	// gl_FragColor = fract(sy) > (1.0 / stripeWidth) ? trgb : vec4(1.0);

	vec4 trgb = texture2D(tDiffuse, vUv);
    float stripeWidth01 =  stripeWidth / resolution.y;
    float sy = vUv.y / stripeWidth01;
	vec4 c = fract(sy) > (1.0 / float(stripeWidth)) ? trgb : (trgb.a > 0.0 ? vec4(1.0) : vec4(trgb.rgb, 1.0));
    // gl_FragColor = isWhite(c) ? vec4(1.0) : vec4(0.0);
    gl_FragColor = c;
}`});
