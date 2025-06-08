declare module '@heroicons/react/outline' {
  export interface IconProps {
    className?: string;
    [key: string]: any; // Allow other props to be passed through
  }

  export const SearchIcon: React.FC<IconProps>;
  export const EyeIcon: React.FC<IconProps>;
  export const TrashIcon: React.FC<IconProps>;
  export const DownloadIcon: React.FC<IconProps>;
  export const TagIcon: React.FC<IconProps>;
}
