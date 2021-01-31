define([], function() {
  return shader = `

  varying vec2 vUv;
uniform vec2 resolution;
uniform float C;
uniform int windowSize;
uniform sampler2D tDiffuse;

void main()	{

  float average = 0.;

  const int windowSizeRounded = 15;
  int nPixelsInWindow = windowSizeRounded * windowSizeRounded;
  const int halfWindowSize = windowSizeRounded / 2;

  for (int xi = -halfWindowSize ; xi <= halfWindowSize ; xi++) {
    for (int yi = -halfWindowSize ; yi <= halfWindowSize ; yi++) {
      average += texture2D(tDiffuse, vUv + ( vec2(xi, yi) / resolution ) ).x;
    }
  }

  average /= float(nPixelsInWindow);

  float t = texture2D(tDiffuse, vUv).x;

  float thresholded = average - C < t ? 1. : 0.;

	gl_FragColor = vec4(thresholded, thresholded, thresholded, 1.);
}`});
