/**
 * Reusable documentation link component
 */

import { Button, Link } from '@mui/material';
import { MenuBook as DocsIcon, OpenInNew as ExternalIcon } from '@mui/icons-material';

interface DocLinkProps {
  href: string;
  text?: string;
  variant?: 'button' | 'link';
  size?: 'small' | 'medium' | 'large';
}

export default function DocLink({ href, text = 'Learn More', variant = 'button', size = 'small' }: DocLinkProps) {
  const isExternal = href.startsWith('http');
  const repoUrl = import.meta.env.VITE_GITHUB_REPO_URL || 'https://github.com/MattVerwey/TopDeck';
  const fullHref = isExternal ? href : `${repoUrl}/blob/main/${href}`;

  if (variant === 'link') {
    return (
      <Link
        href={fullHref}
        target="_blank"
        rel="noopener noreferrer"
        sx={{
          display: 'inline-flex',
          alignItems: 'center',
          gap: 0.5,
          color: 'primary.main',
          textDecoration: 'none',
          '&:hover': {
            textDecoration: 'underline',
          },
        }}
      >
        <DocsIcon fontSize="small" />
        {text}
        {isExternal && <ExternalIcon sx={{ fontSize: 14, ml: 0.5 }} />}
      </Link>
    );
  }

  return (
    <Button
      href={fullHref}
      target="_blank"
      rel="noopener noreferrer"
      startIcon={<DocsIcon />}
      endIcon={isExternal ? <ExternalIcon /> : undefined}
      size={size}
      sx={{ textTransform: 'none' }}
    >
      {text}
    </Button>
  );
}
