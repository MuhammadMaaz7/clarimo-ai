import { useRef } from 'react';
import { Canvas, useFrame } from '@react-three/fiber';
import { Stars, OrbitControls } from '@react-three/drei';
import * as THREE from 'three';

function RotatingCore() {
  const meshRef = useRef<THREE.Group>(null);

  useFrame((state) => {
    if (!meshRef.current) return;
    meshRef.current.rotation.y = state.clock.elapsedTime * 0.2;
    meshRef.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.1) * 0.5;
    
    // Create a pulsing effect
    const scale = 1 + Math.sin(state.clock.elapsedTime * 2) * 0.05;
    meshRef.current.scale.set(scale, scale, scale);
  });

  return (
    <group ref={meshRef}>
      {/* Outer Wireframe Sphere */}
      <mesh>
        <icosahedronGeometry args={[4, 2]} />
        <meshBasicMaterial color="#a78bfa" wireframe transparent opacity={0.3} />
      </mesh>
      
      {/* Inner Glowing Core */}
      <mesh>
        <icosahedronGeometry args={[2.5, 2]} />
        <meshBasicMaterial color="#d8b4fe" wireframe transparent opacity={0.6} />
      </mesh>
      
      {/* Central Solid Core */}
      <mesh>
        <sphereGeometry args={[1.5, 32, 32]} />
        <meshStandardMaterial color="#3b0764" emissive="#a78bfa" emissiveIntensity={0.5} roughness={0.2} metalness={0.8} />
      </mesh>
    </group>
  );
}

function GridFloor() {
  return (
    <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -6, 0]}>
      <planeGeometry args={[100, 100, 40, 40]} />
      <meshBasicMaterial color="#7c3aed" wireframe transparent opacity={0.15} />
    </mesh>
  );
}

export default function Hero3D() {
  return (
    <div className="absolute top-0 left-0 w-screen h-screen z-0 overflow-hidden pointer-events-none bg-black">
      <div className="absolute inset-0 bg-gradient-to-b from-transparent via-background/60 to-background z-10" />
      <Canvas
        camera={{ position: [0, 2, 12], fov: 60 }}
        style={{ width: '100%', height: '100%', position: 'absolute', top: 0, left: 0 }}
        gl={{ antialias: true, alpha: false }}
      >
        <color attach="background" args={['#050508']} />
        <ambientLight intensity={0.5} />
        <pointLight position={[10, 10, 10]} intensity={1} color="#c084fc" />
        <pointLight position={[-10, -10, -10]} intensity={0.5} color="#3b82f6" />
        
        <RotatingCore />
        <GridFloor />
        <Stars radius={100} depth={50} count={5000} factor={4} saturation={1} fade speed={1.5} />
        
        <OrbitControls enableZoom={false} enablePan={false} enableRotate={false} />
      </Canvas>
    </div>
  );
}
