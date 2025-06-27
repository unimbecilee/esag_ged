import { ElementType } from 'react';
import { IconType } from 'react-icons';

export const asElementType = (icon: IconType): ElementType => icon as unknown as ElementType; 
