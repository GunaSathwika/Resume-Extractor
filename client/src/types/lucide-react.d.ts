declare module 'lucide-react' {
  export type IconName = string;
  export type IconProps = React.SVGProps<SVGSVGElement>;
  export const icons: Record<IconName, React.ComponentType<IconProps>>;
  export function LucideIcon(props: IconProps & { name: IconName }): JSX.Element;
  export const FileText: React.FC<IconProps>;
  export const X: React.FC<IconProps>;
}
