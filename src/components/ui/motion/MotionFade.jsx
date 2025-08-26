import React from 'react';
import { motion } from 'framer-motion';

const MotionFade = ({ children, delay = 0, className = '' }) => {
	return (
		<motion.div
			className={className}
			initial={{ opacity: 0 }}
			animate={{ opacity: 1 }}
			transition={{ duration: 0.35, delay }}
		>
			{children}
		</motion.div>
	);
};

export default MotionFade;
