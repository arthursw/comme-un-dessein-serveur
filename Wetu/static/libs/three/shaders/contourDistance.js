define([], function() {
  return shader = `
varying vec2 vUv;
uniform int windowSize;
uniform vec2 resolution;
uniform sampler2D tDiffuse;

void main()	{

  const int windowSizeRounded = 15;
  const int halfWindowSize = windowSizeRounded / 2;
  
  float maxDistance = float(2 * halfWindowSize * halfWindowSize);
  float minDistance = maxDistance;

  for (int xi = -halfWindowSize ; xi <= halfWindowSize ; xi++) {
    for (int yi = -halfWindowSize ; yi <= halfWindowSize ; yi++) {

      vec4 tij = texture2D(tDiffuse, vUv + ( vec2(xi, yi) / resolution ) );
      if(tij.x > 0.5) {
        float distance = float(xi * xi + yi * yi);
        if(distance < minDistance) {
          minDistance = distance;
        }
      }
    }
  }

  minDistance /= maxDistance;
  // float d = 8. * minDistance;
  float d = pow(minDistance, 0.5);
  // float d = minDistance;

	gl_FragColor = vec4(d, d, d, 1.);
}`});
