define([], function() {
	return shader = `
varying vec2 vUv;
uniform vec2 resolution;
uniform sampler2D image;

void main()	{
	float x = mod(gl_FragCoord.x, 20.) < 10. ? 1. : 0.;
	float y = mod(gl_FragCoord.y, 20.) < 10. ? 1. : 0.;
	vec4 t = texture2D(image, vUv);
	gl_FragColor = vec4(x, y, t.r, 1.);
}`});
