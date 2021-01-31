define([], function() {
	return shader = `#version 300 es

precision highp float;

in vec2 vUv;
out vec4 fragColor;

uniform vec2 mousePosition;
uniform vec2 resolution;
uniform sampler2D tDiffuse;

float colorToGrayscale(vec4 c) {
	return 0.2126 * c.r + 0.7153 * c.g + 0.0721 * c.b;
}

vec3 hsv2rgb(vec3 c) {
    vec4 K = vec4(1.0, 2.0 / 3.0, 1.0 / 3.0, 3.0);
    vec3 p = abs(fract(c.xxx + K.xyz) * 6.0 - K.www);
    return c.z * mix(K.xxx, clamp(p - K.xxx, 0.0, 1.0), c.y);
}

vec4 hsv2rgb(vec4 c) {
    return vec4(hsv2rgb(c.xyz), c.w);
}

vec3 rgb2hsv(vec3 c) {
    vec4 K = vec4(0.0, -1.0 / 3.0, 2.0 / 3.0, -1.0);
    vec4 p = mix(vec4(c.bg, K.wz), vec4(c.gb, K.xy), step(c.b, c.g));
    vec4 q = mix(vec4(p.xyw, c.r), vec4(c.r, p.yzx), step(p.x, c.r));

    float d = q.x - min(q.w, q.y);
    float e = 1.0e-10;
    return vec3(abs(q.z + (q.w - q.y) / (6.0 * d + e)), d / (q.x + e), q.x);
}

vec4 rgb2hsv(vec4 c) {
    return vec4(rgb2hsv(c.xyz), c.w);
}


void main()	{
	vec4 t = texture(tDiffuse, vUv);
    float grayscale = colorToGrayscale(t);
	vec4 hsv = rgb2hsv(t);
	float c = grayscale < 0.3 ? grayscale : 1. - hsv.g;
    float f = c;
    // float f = vUv.x < mousePosition.x && vUv.y < mousePosition.y ? 1. - grayscale :
    //           vUv.x > mousePosition.x && vUv.y < mousePosition.y ? 1. - hsv.r : 
    //           vUv.x < mousePosition.x && vUv.y > mousePosition.y ? hsv.g : 
    //           vUv.x > mousePosition.x && vUv.y > mousePosition.y ? 1. - hsv.b : 0.;
    // float f = vUv.x < mousePosition.x ? hsv.b : 1. - hsv.g;
    // float f = hsv.b < 0.3 || hsv.g > 0.3 ? 0. : 1.;
    fragColor = vec4(f, f, f, 1.);
}`});
