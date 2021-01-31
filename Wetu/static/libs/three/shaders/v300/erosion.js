define([], function() {
	return shader = `#version 300 es

precision highp float;

in vec2 vUv;
out vec4 fragColor;

uniform vec2 resolution;
uniform sampler2D tDiffuse;

void main()	{
    float threshold = 0.5;
	vec4 trgb = texture(tDiffuse, vUv);
	bool t = trgb.r < threshold;
	bool txm1 = texture(tDiffuse, vUv - vec2(1., 0.) / resolution).x < threshold;
	bool tym1 = texture(tDiffuse, vUv - vec2(0., 1.) / resolution).x < threshold;
	
	bool txp1 = texture(tDiffuse, vUv + vec2(1., 0.) / resolution).x < threshold;
	bool typ1 = texture(tDiffuse, vUv + vec2(0., 1.) / resolution).x < threshold;
	
	bool previousF = trgb.g > threshold && trgb.b < threshold;
	// float f = previousF || t && (!txm1 && !txp1 || !tym1 && !typ1) ? 1. : 0.;
	// float c = !t || (txm1 != txp1 || tym1 != typ1) ? 1. : 0.;
	// fragColor = vec4(c, f, 0., 1.);

	bool txm2 = texture(tDiffuse, vUv - vec2(2., 0.) / resolution).x < threshold;
	bool tym2 = texture(tDiffuse, vUv - vec2(0., 2.) / resolution).x < threshold;

	bool txp2 = texture(tDiffuse, vUv + vec2(2., 0.) / resolution).x < threshold;
	bool typ2 = texture(tDiffuse, vUv + vec2(0., 2.) / resolution).x < threshold;

	float f = previousF || t && ( ( !txm2 || !txm1 ) && ( !txp1 || !txp2 ) || ( !tym2 || !tym1 ) && ( !typ1 || !typ2 ) ) ? 1. : 0.;
	bool h = !txm1 && !txm2 && (txp1 || txp2) || !txp1 && !txp2 && (txm1 || txm2);
	bool v = !tym1 && !tym2 && (typ1 || typ2) || !typ1 && !typ2 && (tym1 || tym2);
	float c = !t || (h || v) ? 1. : 0.;
	fragColor = vec4(c, f, 0., 1.);
}`});
